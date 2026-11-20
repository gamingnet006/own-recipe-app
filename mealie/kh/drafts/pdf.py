"""KH: reads a PDF for the drafts intake (D84): a PDF with a text layer gives its text, a scanned one the page images
it embeds (pypdf cannot render pages). Nothing is stored here; file_import turns the result into drafts."""

import io
from dataclasses import dataclass
from time import monotonic

from PIL.Image import Image as PilImage
from pypdf import PageObject, PdfReader

from mealie.kh.features.settings import KhSettings

MIN_TEXT_CHARS = 200  # fewer letters than this and the PDF counts as a scan with a little text on it
JPEG_QUALITY = 90  # extracted scans are re-encoded, because PDFs hold TIFF, JPEG 2000 and CMYK that drafts do not take


@dataclass
class PdfBudget:
    """What one request may spend on PDFs, shared by all PDFs in it: pages to read and a time limit."""

    pages: int
    deadline: float

    @classmethod
    def from_settings(cls, settings: KhSettings) -> PdfBudget:
        """A fresh budget of PDF_MAX_PAGES pages and PDF_MAX_SECONDS seconds, counted from now."""
        return cls(settings.pdf_max_pages, monotonic() + settings.pdf_max_seconds)

    def out_of_time(self) -> bool:
        """Whether the time limit has passed."""
        return monotonic() >= self.deadline


def is_pdf(data: bytes) -> bool:
    """Whether DATA starts like a PDF."""
    return data.startswith(b"%PDF-")


def _jpeg(image: PilImage) -> bytes:
    """IMAGE as an RGB JPEG, whatever colour model the PDF stored it in."""
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue()


def _read_text(reader: PdfReader, budget: PdfBudget) -> tuple[list[PageObject], str, bool]:
    """(pages read, their text, whether the budget stopped the reading) of the pages the budget allows."""
    pages: list[PageObject] = []
    parts: list[str] = []
    for page in reader.pages:
        if budget.pages <= 0 or budget.out_of_time():
            return pages, "\n".join(parts).strip(), True
        budget.pages -= 1
        pages.append(page)
        parts.append(page.extract_text() or "")
    return pages, "\n".join(parts).strip(), False


def _read_images(pages: list[PageObject], budget: PdfBudget, limit: int) -> tuple[list[bytes], bool]:
    """(up to LIMIT images as JPEG, whether the time limit stopped the reading). Each image is checked before it is
    decoded, because one page can list thousands; an image that cannot be decoded is skipped, not the PDF."""
    images: list[bytes] = []
    for page in pages:
        for image in page.images:
            if len(images) >= limit:
                return images, False
            if budget.out_of_time():
                return images, True
            try:
                images.append(_jpeg(image.image))
            except Exception:  # noqa: BLE001, S112 - pypdf and PIL fail in many ways on odd scans; try the next one
                continue
    return images, False


def read_pdf(data: bytes, settings: KhSettings, budget: PdfBudget) -> tuple[str, list[bytes]]:
    """(text, images) of the pages BUDGET allows: the text if it holds MIN_TEXT_CHARS non-space characters, else the
    embedded images (at most DRAFT_MAX_IMAGES, as JPEG). A PDF locked only by an empty password is opened. Raises
    ValueError("pdf_encrypted"), ("unreadable") for a damaged file, ("pdf_too_slow") when the budget ran out before
    anything usable, or ("pdf_unreadable") when there is neither text nor an image to use."""
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ValueError("pdf_encrypted")
        pages, text, stopped = _read_text(reader, budget)
        if len("".join(text.split())) >= MIN_TEXT_CHARS:
            return text, []
        images, timed_out = _read_images(pages, budget, settings.draft_max_images)
    except ValueError as error:
        if str(error) == "pdf_encrypted":
            raise
        raise ValueError("unreadable") from error
    except Exception as error:  # pypdf raises many kinds of errors on damaged files; all mean "cannot read it"
        raise ValueError("unreadable") from error
    if not images:
        raise ValueError("pdf_too_slow" if stopped or timed_out else "pdf_unreadable")
    return "", images
