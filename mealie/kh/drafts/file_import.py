"""KH: reads an uploaded file for the drafts intake (D62): a .txt or .md file is one text, a .pdf its text or scanned
pages (D84), a .zip is unpacked in memory into texts, PDFs and photos, with the limits that stop a ZIP bomb.
Nothing is stored here; the service makes drafts."""

import io
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from mealie.kh.drafts.pdf import PdfBudget, read_pdf
from mealie.kh.drafts.schemas import SkippedFile
from mealie.kh.features.settings import KhSettings

TEXT_SUFFIXES = {".txt", ".md"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
ZIP_ERRORS = (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError)  # RuntimeError: password
MB = 1024 * 1024
CHUNK = 64 * 1024  # unpacked piece by piece, so a bomb is stopped at the limit and never held in memory


@dataclass
class FileItem:
    """One future draft: a text (with the photo of the same name, if any) or photos alone (a scanned PDF brings
    several); NAME is the file's."""

    name: str
    text: str | None = None
    photos: list[bytes] = field(default_factory=list)


@dataclass
class FileContent:
    """What a file holds: the items to turn into drafts and the entries that cannot be used."""

    items: list[FileItem] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)


def decode_text(data: bytes) -> str | None:
    """The text as UTF-8, else as Windows-1252 (old Windows editors); None if neither reads it."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def is_hidden(name: str) -> bool:
    """macOS's __MACOSX folder, "._" copies and .DS_Store, and any other dot file or folder."""
    return any(part.startswith(".") or part == "__MACOSX" for part in PurePosixPath(name).parts)


def read_zip(data: bytes, settings: KhSettings) -> list[tuple[str, bytes]]:
    """The files of a ZIP as (name, content), sorted by name. Raises ValueError("broken_zip") or
    ValueError("zip_too_large"): the sizes the ZIP declares are summed first (cheap filter), then the real size is
    counted while unpacking in chunks, because a ZIP may declare less than it holds."""
    limit = settings.import_max_unzipped_mb * MB
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir() and not is_hidden(info.filename)]
            if sum(info.file_size for info in infos) > limit:
                raise ValueError("zip_too_large")
            files: list[tuple[str, bytes]] = []
            total = 0
            for info in sorted(infos, key=lambda info: info.filename):
                chunks: list[bytes] = []
                with archive.open(info) as entry:
                    while chunk := entry.read(CHUNK):
                        total += len(chunk)
                        if total > limit:
                            raise ValueError("zip_too_large")
                        chunks.append(chunk)
                files.append((info.filename, b"".join(chunks)))
            return files
    except ZIP_ERRORS as error:
        raise ValueError("broken_zip") from error


def _skip(content: FileContent, name: str, reason: str) -> None:
    """Notes an entry that cannot become a draft."""
    content.skipped.append(SkippedFile(name=name, reason=reason))


def _add_text(
    content: FileContent, texts: dict[tuple[PurePosixPath, str], FileItem], name: str, text: str, limit: int
) -> None:
    """Adds TEXT as an item of its own, or skips it as empty or too long; it can be given a photo of its name."""
    text = text.strip()
    if not text:
        _skip(content, name, "empty")
    elif len(text) > limit:
        _skip(content, name, "text_too_long")
    else:
        path = PurePosixPath(name)
        item = FileItem(name=name, text=text)
        texts[(path.parent, path.stem.lower())] = item
        content.items.append(item)


def _add_pdf(
    content: FileContent,
    texts: dict[tuple[PurePosixPath, str], FileItem],
    name: str,
    raw: bytes,
    settings: KhSettings,
    budget: PdfBudget,
) -> None:
    """Adds a PDF as a text item, or as a photo item of its embedded images; what cannot be read is skipped."""
    try:
        text, images = read_pdf(raw, settings, budget)
    except ValueError as error:
        _skip(content, name, str(error))
        return
    if text:
        _add_text(content, texts, name, text, settings.draft_max_text)
    else:
        content.items.append(FileItem(name=name, photos=images))


def read_file(filename: str, data: bytes, settings: KhSettings) -> FileContent:
    """The items of an uploaded file. A .zip is paired by folder and name without the suffix: a photo with the name
    of a text belongs to it (the first one; more photos of the same name are photos of their own). The first
    IMPORT_MAX_DRAFTS items count, the rest is skipped as "too_many". Raises ValueError for a ZIP that cannot be
    read or is too large."""
    suffix = PurePosixPath(filename).suffix.lower()
    files = read_zip(data, settings) if suffix == ".zip" else [(filename, data)]
    content = FileContent()
    budget = PdfBudget.from_settings(settings)  # one for all PDFs of this upload
    texts: dict[tuple[PurePosixPath, str], FileItem] = {}
    photos: list[tuple[str, bytes]] = []
    for name, raw in files:
        path = PurePosixPath(name)
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = decode_text(raw)
            if text is None:
                _skip(content, name, "unreadable")
            else:
                _add_text(content, texts, name, text, settings.draft_max_text)
        elif path.suffix.lower() == ".pdf":
            _add_pdf(content, texts, name, raw, settings, budget)
        elif path.suffix.lower() in IMAGE_SUFFIXES:
            photos.append((name, raw))
        else:
            _skip(content, name, "unsupported")
    for name, raw in photos:
        path = PurePosixPath(name)
        owner = texts.get((path.parent, path.stem.lower()))
        if owner and not owner.photos:
            owner.photos.append(raw)
        else:
            content.items.append(FileItem(name=name, photos=[raw]))
    for item in content.items[settings.import_max_drafts :]:
        _skip(content, item.name, "too_many")
    del content.items[settings.import_max_drafts :]
    return content
