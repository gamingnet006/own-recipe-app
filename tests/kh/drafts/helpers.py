"""KH: small helpers for the drafts tests: generated images (never real photos) and API calls."""

import io
import os
import zipfile

import pillow_heif
from fastapi.testclient import TestClient
from httpx import Response
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from tests.utils.fixture_schemas import TestUser

DRAFTS = "/api/kh/drafts"


def png(width: int, height: int, *, noise: bool = False) -> bytes:
    """A PNG of the given size; noise makes it large, because random pixels hardly compress."""
    if noise:
        image = Image.frombytes("RGB", (width, height), os.urandom(width * height * 3))
    else:
        image = Image.new("RGB", (width, height), (200, 120, 40))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def heic(width: int, height: int) -> bytes:
    """A HEIC image as iPhones take them."""
    buffer = io.BytesIO()
    pillow_heif.from_pillow(Image.new("RGB", (width, height), (40, 120, 200))).save(buffer, quality=50)
    return buffer.getvalue()


def post_draft(api_client: TestClient, user: TestUser, **kwargs) -> Response:
    """POST /api/kh/drafts with form data and files, as the intake page sends them."""
    return api_client.post(DRAFTS, headers=user.token, **kwargs)


def get_draft(api_client: TestClient, user: TestUser, draft_id: str) -> Response:
    """GET one draft."""
    return api_client.get(f"{DRAFTS}/{draft_id}", headers=user.token)


def open_ids(api_client: TestClient, user: TestUser) -> list[str]:
    """IDs of the drafts the user's household has not approved yet."""
    return [draft["id"] for draft in api_client.get(DRAFTS, headers=user.token).json()]


def zip_bytes(files: dict[str, bytes]) -> bytes:
    """A ZIP of the given files (name to content), as the Files app or Finder would make one."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def post_file(api_client: TestClient, user: TestUser, name: str, content: bytes) -> Response:
    """POST /api/kh/drafts/file with one uploaded file, as the intake page sends it."""
    return api_client.post(f"{DRAFTS}/file", headers=user.token, files={"file": (name, content)})


def pdf_with_text(lines: list[str], *, password: str | None = None) -> bytes:
    """A one-page PDF with a text layer, one line of LINES under the other; PASSWORD
    (may be empty) is the one the PDF asks for."""
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(("BT /F1 10 Tf 40 750 Td 14 TL " + " ".join(f"({line}) '" for line in lines) + " ET").encode())
    page[NameObject("/Contents")] = writer._add_object(stream)
    if password is not None:
        writer.encrypt(password, owner_password="owner", algorithm="RC4-128")
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def pdf_scan(*sizes: tuple[int, int], mode: str = "RGB") -> bytes:
    """A PDF with one page per size that holds only an image (of colour MODE, e.g. "CMYK" or "1") and no text, as a
    scanner makes it."""
    pages = [Image.new(mode, size, 0) for size in sizes]
    buffer = io.BytesIO()
    pages[0].save(buffer, format="PDF", save_all=True, append_images=pages[1:])
    return buffer.getvalue()


def pdf_with_repeated_image(count: int) -> bytes:
    """A one-page PDF whose resources list the same image COUNT times under different names."""
    writer = PdfWriter()
    page = writer.add_blank_page(100, 100)
    reader = PdfReader(io.BytesIO(pdf_scan((20, 20))))
    image = reader.pages[0]["/Resources"]["/XObject"]
    ref = next(iter(image.values()))
    clone = writer._add_object(ref.get_object().clone(writer))
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/XObject"): DictionaryObject({NameObject(f"/Im{n}"): clone for n in range(count)})}
    )
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
