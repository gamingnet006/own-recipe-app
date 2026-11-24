"""KH: decides what a share from the iOS Shortcuts app is (D84). Shortcuts cannot branch on the kind of its input, so
one request carries files, text and url and this module picks the source of the draft. Pure functions, no I/O."""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath

from mealie.kh.drafts.pdf import is_pdf
from mealie.kh.i18n.locale import DEFAULT_LOCALE, Locale
from mealie.kh.i18n.messages import MESSAGES, say

# Same address rule and message length as the frontend's readSharedImport (D57, frontend/kh/app/lib/shared-import.ts):
# keep the two in sync.
WEB_ADDRESS = re.compile(r"https?://\S*[^\s.,;:!?)»]", re.IGNORECASE)
SHARE_MESSAGE_MAX = 200  # characters around the one link that still make a share message, not a recipe
CAPTION_MIN = 20  # characters a text next to photos needs to be more than the photos' names Shortcuts puts there

HEIF_BRANDS = {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"}
TEXT_SUFFIXES = {".txt", ".md"}
SNIFF_BYTES = 16  # how much of a file's start the decision reads


class ShareKind(StrEnum):
    """What the share becomes."""

    photo = "photo"
    pdf = "pdf"
    file = "file"
    link = "link"
    text = "text"


@dataclass
class SharedFile:
    """One file of a share: its NAME, its first bytes (HEAD) and, for a .txt or .md file, its TEXT."""

    name: str
    head: bytes
    text: str | None = None


@dataclass
class ShareDecision:
    """KIND and what the draft is made from: the link in VALUE for a link, the text for a text, the file name to read
    the file by (suffix fixed to what it is) for pdf and file (FILE is its index). A photo draft takes all the photos
    (IMAGES, indexes in the order sent) and the text that came with them (CAPTION), e.g. a note with its photos."""

    kind: ShareKind
    value: str
    file: int = 0
    images: list[int] = field(default_factory=list)
    caption: str | None = None


def is_image(head: bytes) -> bool:
    """Whether HEAD (the first bytes of a file) is a JPEG, PNG, WebP or HEIC image; the name is not trusted. A GIF is
    not one: drafts do not take it, so a shared GIF is ignored and the text or link that comes with it counts."""
    return (
        head.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"))
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
        or (head[4:8] == b"ftyp" and head[8:12] in HEIF_BRANDS)
    )


def _file_decision(filename: str, head: bytes) -> ShareDecision | None:
    """What an attached file other than a photo is, or None for one to ignore (a Safari web page, a web archive,
    anything else). Only a file that starts like a ZIP and is named .zip (or has no suffix) is a ZIP: .docx, .pages
    and .epub are ZIPs too."""
    stem, suffix = PurePosixPath(filename).stem, PurePosixPath(filename).suffix.lower()
    if is_pdf(head):
        return ShareDecision(ShareKind.pdf, f"{stem or 'share'}.pdf")
    if head.startswith(b"PK\x03\x04") and suffix in {".zip", ""}:
        return ShareDecision(ShareKind.file, f"{stem or 'share'}.zip")
    if suffix in TEXT_SUFFIXES:
        return ShareDecision(ShareKind.file, filename)
    return None


def _addresses(text: str) -> list[str]:
    """The distinct http(s) addresses in TEXT, in order."""
    return list(dict.fromkeys(WEB_ADDRESS.findall(text)))


def _caption(text: str, files: list[SharedFile]) -> str | None:
    """The text that came with photos, or None when it is only the files' names (Shortcuts turns a photo into its
    name when it fills a text field). A text that came only as a .txt file counts too."""
    text = text or next((file.text.strip() for file in files if file.text and file.text.strip()), "")
    names = {name for file in files for name in (file.name, PurePosixPath(file.name).stem) if name}
    kept = [line for line in text.splitlines() if line.strip() not in names]
    rest = "\n".join(kept).strip()
    without_names = rest
    for name in sorted(names, key=len, reverse=True):
        without_names = without_names.replace(name, "")
    return rest if len("".join(without_names.split())) >= CAPTION_MIN else None


def classify_share(files: list[SharedFile], text: str | None, url: str | None) -> ShareDecision | None:
    """What a share is, or None when nothing in it is usable. Photos win and all of them make one draft with the text
    that came along; then the first usable other file; then one link with a short message (or none) is a link, a
    longer text a text, and a list of links without text the first link. Shortcuts sends a shared text also as a
    .txt file, so a text file wins only when the text field is empty or says something else."""
    text = (text or "").strip()
    images = [n for n, file in enumerate(files) if is_image(file.head)]
    if images:
        return ShareDecision(ShareKind.photo, files[images[0]].name, images=images, caption=_caption(text, files))
    for n, file in enumerate(files):
        decision = _file_decision(file.name, file.head)
        if decision is None:
            continue
        decision.file = n
        if decision.kind != ShareKind.file or not file.name.lower().endswith(tuple(TEXT_SUFFIXES)):
            return decision
        if not text or (file.text or "").strip() != text:
            return decision
    in_url = _addresses(url or "")
    if len(in_url) == 1 and len(text.replace(in_url[0], "").strip()) <= SHARE_MESSAGE_MAX:
        return ShareDecision(ShareKind.link, in_url[0])
    in_text = _addresses(text)
    if len(in_text) == 1 and len(text.replace(in_text[0], "").strip()) <= SHARE_MESSAGE_MAX:
        return ShareDecision(ShareKind.link, in_text[0])
    if text:
        return ShareDecision(ShareKind.text, text)
    return ShareDecision(ShareKind.link, in_url[0]) if in_url else None


def share_confirmation(created: int, locale: Locale = DEFAULT_LOCALE) -> str:
    """The sentence the shortcut says after a share made `created` drafts (D88), in LOCALE."""
    return say("share_done_one" if created == 1 else "share_done_many", locale, count=created)


def skip_reason(reason: str, locale: Locale = DEFAULT_LOCALE) -> str:
    """Why a shared file was skipped, in words the shortcut shows as they are; an unknown reason gets a general text."""
    key = f"skip_{reason}"  # the reasons the drafts service names each have a sentence in messages.py
    return say(key if key in MESSAGES else "skip_other", locale)
