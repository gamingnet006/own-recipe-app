"""KH: decides what a share from the iOS Shortcuts app is (D84). Shortcuts cannot branch on the kind of its input, so
one request carries file, text and url and this module picks the one source of the draft. Pure functions, no I/O."""

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from mealie.kh.drafts.pdf import is_pdf

# Same address rule and message length as the frontend's readSharedImport (D57, frontend/kh/app/lib/shared-import.ts):
# keep the two in sync.
WEB_ADDRESS = re.compile(r"https?://\S*[^\s.,;:!?)»]", re.IGNORECASE)
SHARE_MESSAGE_MAX = 200  # characters around the one link that still make a share message, not a recipe

HEIF_BRANDS = {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"}
TEXT_SUFFIXES = {".txt", ".md"}
SKIP_REASONS = {  # German sentences for the skip reasons, because the shortcut shows the answer as it is
    "too_large": "zu groß",
    "not_an_image": "kein Foto",
    "unreadable": "nicht lesbar",
    "empty": "leer",
    "text_too_long": "Text zu lang",
    "unsupported": "Dateityp nicht unterstützt",
    "too_many": "zu viele Dateien",
    "pdf_encrypted": "PDF mit Passwort",
    "pdf_unreadable": "kein Text und kein Bild im PDF",
    "pdf_too_slow": "PDF zu aufwendig",
}
SNIFF_BYTES = 16  # how much of a file's start the decision reads


class ShareKind(StrEnum):
    """What the share becomes."""

    photo = "photo"
    pdf = "pdf"
    file = "file"
    link = "link"
    text = "text"


@dataclass
class ShareDecision:
    """KIND and the one thing the draft is made from: the link in VALUE for a link, the text for a text, the
    file name to read the file by (suffix fixed to what it is) for photo, pdf and file."""

    kind: ShareKind
    value: str


def is_image(head: bytes) -> bool:
    """Whether HEAD (the first bytes of a file) is a JPEG, PNG, WebP or HEIC image; the name is not trusted. A GIF is
    not one: drafts do not take it, so a shared GIF is ignored and the text or link that comes with it counts."""
    return (
        head.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"))
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
        or (head[4:8] == b"ftyp" and head[8:12] in HEIF_BRANDS)
    )


def _file_decision(filename: str, head: bytes) -> ShareDecision | None:
    """What an attached file is, or None for one to ignore (a Safari web page, a web archive, anything else). Only a
    file that starts like a ZIP and is named .zip (or has no suffix) is a ZIP: .docx, .pages and .epub are ZIPs too."""
    if is_image(head):
        return ShareDecision(ShareKind.photo, filename)
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


def classify_share(
    filename: str | None, head: bytes, text: str | None, url: str | None, file_text: str | None = None
) -> ShareDecision | None:
    """What a share is, or None when nothing in it is usable. A usable file wins; then one link with a short message
    (or none) is a link, a longer text a text, and a list of links without text the first link. Shortcuts sends a
    shared text also as a .txt file, so a text file (its content is FILE_TEXT) wins only when the text field is
    empty or says something else."""
    text = (text or "").strip()
    if filename is not None and (decision := _file_decision(filename, head)):
        if decision.kind != ShareKind.file or not filename.lower().endswith(tuple(TEXT_SUFFIXES)):
            return decision
        if not text or (file_text or "").strip() != text:
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
