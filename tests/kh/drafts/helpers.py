"""KH: small helpers for the drafts tests: generated images (never real photos) and API calls."""

import io
import os
import zipfile

import pillow_heif
from fastapi.testclient import TestClient
from httpx import Response
from PIL import Image

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
