"""KH: tests for the file import (D62): .txt and .md files and ZIP folders become drafts without anything stored on
disk but the photos, with limits against ZIP bombs; a photo with a text's name is that draft's cover."""

import asyncio
from datetime import timedelta

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts import recognize
from mealie.kh.drafts.file_import import read_file, read_zip
from mealie.kh.drafts.files import draft_dir
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import DraftStatus
from mealie.kh.features.settings import get_kh_settings
from tests.kh.drafts.helpers import DRAFTS, get_draft, open_ids, png, post_file, zip_bytes
from tests.kh.drafts.test_kh_drafts_text_format import EXPORT
from tests.utils.fixture_schemas import TestUser

TEXT = "Testkuchen: 200 g Mehl, 100 g Zucker, 3 Eier. 30 Minuten backen."


def reasons(content) -> dict[str, str]:
    return {skipped.name: skipped.reason for skipped in content.skipped}


def test_text_file_is_one_text_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai("recipe.json")
    response = post_file(api_client, unique_user, "kuchen.txt", TEXT.encode())
    assert response.status_code == 201
    body = response.json()
    assert body["skipped"] == [] and len(body["created"]) == 1
    draft = get_draft(api_client, unique_user, body["created"][0]["id"]).json()
    assert draft["status"] == "ready" and draft["sourceType"] == "text" and draft["sourceText"] == TEXT
    assert len(calls) == 1


def test_kochheft_text_file_needs_no_ai(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai(Exception("the AI must not be called"))
    response = post_file(api_client, unique_user, "Testkuchen.md", EXPORT.encode())
    draft = get_draft(api_client, unique_user, response.json()["created"][0]["id"]).json()
    assert draft["status"] == "ready" and draft["aiModel"] is None
    assert calls == []


def test_non_utf8_text_is_read_as_windows_1252(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    response = post_file(api_client, unique_user, "kuchen.txt", "Käsekuchen: 3 Eier".encode("cp1252"))
    draft = get_draft(api_client, unique_user, response.json()["created"][0]["id"]).json()
    assert draft["sourceText"] == "Käsekuchen: 3 Eier"


def test_zip_with_text_photo_pair_and_lone_photo(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    archive = zip_bytes(
        {
            "Buch/Kuchen.txt": EXPORT.encode(),
            "Buch/kuchen.png": png(40, 30),
            "Buch/Zettel.png": png(40, 30),
            "Buch/Notizen.md": TEXT.encode(),
            "Buch/Buch.pdf": b"%PDF",
        }
    )
    response = post_file(api_client, unique_user, "Buch.zip", archive)
    assert response.status_code == 201
    body = response.json()
    assert body["skipped"] == [{"name": "Buch/Buch.pdf", "reason": "unsupported"}]
    by_note = {draft["sourceNote"]: draft for draft in body["created"]}
    assert set(by_note) == {"Kuchen.txt", "Notizen.md", "Zettel.png"}
    paired = get_draft(api_client, unique_user, by_note["Kuchen.txt"]["id"]).json()
    assert paired["sourceType"] == "text" and paired["originalFiles"] == ["original-1.webp"]
    assert (draft_dir(paired["id"]) / "original-1.webp").exists()
    lone = get_draft(api_client, unique_user, by_note["Zettel.png"]["id"]).json()
    assert lone["sourceType"] == "image" and lone["originalFiles"] == ["original-1.webp"]
    assert get_draft(api_client, unique_user, by_note["Notizen.md"]["id"]).json()["originalFiles"] == []


def test_paired_photo_becomes_the_recipe_cover(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai(Exception("the AI must not be called"))
    archive = zip_bytes({"Kuchen.txt": EXPORT.encode(), "Kuchen.png": png(40, 30)})
    draft_id = post_file(api_client, unique_user, "x.zip", archive).json()["created"][0]["id"]
    slug = api_client.post(f"{DRAFTS}/{draft_id}/approve", headers=unique_user.token).json()["slug"]
    recipe = api_client.get(f"/api/recipes/{slug}", headers=unique_user.token).json()
    assert recipe["image"]


def test_hidden_files_are_ignored(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    archive = zip_bytes(
        {
            "__MACOSX/._Kuchen.txt": b"\x00\x05",
            "._Kuchen.txt": b"\x00\x05",
            ".DS_Store": b"\x00",
            "Kuchen.txt": TEXT.encode(),
        }
    )
    body = post_file(api_client, unique_user, "x.zip", archive).json()
    assert len(body["created"]) == 1 and body["skipped"] == []


def test_entries_that_do_not_fit_are_named():
    settings = get_kh_settings().model_copy(update={"draft_max_text": 50})
    archive = zip_bytes(
        {
            "a.txt": b"x" * 60,
            "b.txt": b"  \n ",
            "c.txt": b"\xff\x81\x8d",
            "d.png": b"not an image at all",
            "e.docx": b"PK",
        }
    )
    content = read_file("x.zip", archive, settings)
    assert reasons(content) == {
        "a.txt": "text_too_long",
        "b.txt": "empty",
        "c.txt": "unreadable",
        "e.docx": "unsupported",
    }
    assert [item.name for item in content.items] == [
        "d.png"
    ]  # only the picture's content decides: draft creation names it


def test_not_an_image_is_skipped_by_the_route(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    body = post_file(api_client, unique_user, "x.zip", zip_bytes({"d.png": b"nope", "e.txt": TEXT.encode()})).json()
    assert body["skipped"] == [{"name": "d.png", "reason": "not_an_image"}]
    assert len(body["created"]) == 1


def test_too_many_entries_are_cut(api_client: TestClient, unique_user: TestUser, fake_ai, monkeypatch):
    fake_ai("recipe.json")
    monkeypatch.setattr(get_kh_settings(), "import_max_drafts", 2)
    archive = zip_bytes({f"r{n}.txt": TEXT.encode() for n in range(4)})
    body = post_file(api_client, unique_user, "x.zip", archive).json()
    assert [draft["sourceNote"] for draft in body["created"]] == ["r0.txt", "r1.txt"]
    assert body["skipped"] == [{"name": "r2.txt", "reason": "too_many"}, {"name": "r3.txt", "reason": "too_many"}]


def test_too_large_unzipped_creates_nothing(api_client: TestClient, unique_user: TestUser, fake_ai, monkeypatch):
    fake_ai("recipe.json")
    monkeypatch.setattr(get_kh_settings(), "import_max_unzipped_mb", 1)
    before = open_ids(api_client, unique_user)
    bomb = zip_bytes({"a.txt": b"a" * (1024 * 1024 + 1)})  # compresses to a few bytes, unpacks to over the limit
    response = post_file(api_client, unique_user, "x.zip", bomb)
    assert response.status_code == 400 and response.json()["detail"]["code"] == "zip_too_large"
    assert open_ids(api_client, unique_user) == before


def test_too_large_upload_is_refused(api_client: TestClient, unique_user: TestUser, monkeypatch):
    monkeypatch.setattr(get_kh_settings(), "import_max_unzipped_mb", 1)
    response = post_file(api_client, unique_user, "x.txt", b"a" * (1024 * 1024 + 1))
    assert response.status_code == 400 and response.json()["detail"]["code"] == "file_too_large"


def test_broken_zip_is_refused(api_client: TestClient, unique_user: TestUser):
    response = post_file(api_client, unique_user, "x.zip", b"this is not a zip")
    assert response.status_code == 400 and response.json()["detail"]["code"] == "broken_zip"


def test_other_household_cannot_see_the_drafts(
    api_client: TestClient, unique_user: TestUser, h2_user: TestUser, fake_ai
):
    fake_ai("recipe.json")
    draft_id = post_file(api_client, unique_user, "kuchen.txt", TEXT.encode()).json()["created"][0]["id"]
    assert draft_id in open_ids(api_client, unique_user)
    assert open_ids(api_client, h2_user) == []
    assert get_draft(api_client, h2_user, draft_id).status_code == 404


def lying_zip() -> bytes:
    """A ZIP whose only entry declares 1 byte but holds about 2 MB of zeros as a deflate stream."""
    data = bytearray(zip_bytes({"a.txt": b"\0" * (2 * 1024 * 1024)}))
    for signature, at in ((b"PK\x03\x04", 22), (b"PK\x01\x02", 24)):  # uncompressed size in both headers
        start = data.index(signature)
        data[start + at : start + at + 4] = (1).to_bytes(4, "little")
    return bytes(data)


def test_zip_that_declares_less_than_it_holds_is_refused():
    settings = get_kh_settings().model_copy(update={"import_max_unzipped_mb": 1})
    with pytest.raises(ValueError, match="zip_too_large|broken_zip"):
        read_zip(lying_zip(), settings)


def test_queued_recognitions_are_kept_from_going_stale(session, unique_user: TestUser, monkeypatch):
    repo = drafts_repo(session, unique_user.group_id, unique_user.household_id)
    old = get_utc_now() - timedelta(hours=1)
    ids = []
    for n in range(3):
        draft = repo.create(
            {
                "group_id": unique_user.group_id,
                "household_id": unique_user.household_id,
                "user_id": unique_user.user_id,
                "status": DraftStatus.working,
                "source_type": "text",
                "source_text": f"Rezept {n}",
            }
        )
        ids.append(draft.id)
    session.execute(sa.update(KhDraft).values(update_at=old))
    session.commit()
    seen = []

    async def fake_recognize(draft_id, **kwargs):
        session.expire_all()
        seen.append(session.get(KhDraft, draft_id).update_at)

    monkeypatch.setattr(recognize, "recognize", fake_recognize)
    asyncio.run(recognize.recognize_all(ids, user=None, household=None, translator=None))
    assert len(seen) == 3 and all(stamp > old for stamp in seen)
