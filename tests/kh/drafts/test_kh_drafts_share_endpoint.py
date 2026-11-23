"""KH: tests for the one share endpoint (D84): the decision table of classify_share, and POST /drafts/share creating
the draft the decision names."""

import pytest
from fastapi.testclient import TestClient

from mealie.kh.drafts.share import SharedFile, ShareKind, classify_share, share_confirmation
from mealie.kh.features.settings import get_kh_settings
from tests.kh.drafts.helpers import DRAFTS, heic, pdf_scan, pdf_with_text, png, zip_bytes
from tests.kh.drafts.test_kh_drafts_pdf import LINES
from tests.utils.fixture_schemas import TestUser

LINK = "https://example.org/kuchen"
LONG = "Kuchen: " + "200 g Mehl, 100 g Zucker. " * 12


def decide(filename=None, head=b"", text=None, url=None, file_text=None):
    files = [SharedFile(filename, head, file_text)] if filename is not None else []
    decision = classify_share(files, text, url)
    return decision and (decision.kind, decision.value)


JPEG = b"\xff\xd8\xff\xe0 rest"
NOTE = "Omas Apfelkuchen\n200 g Mehl, 100 g Butter, 3 Äpfel.\nAlles verrühren und 40 Minuten backen."


def test_photos_with_a_note_are_one_photo_draft_that_keeps_the_text():
    """A note from the Notes app comes as its text plus its photos: every photo and the text belong to one draft."""
    files = [SharedFile("IMG_1.jpeg", JPEG), SharedFile("Notiz.pdf", b"%PDF-1.7"), SharedFile("IMG_2.jpeg", JPEG)]
    decision = classify_share(files, f"{NOTE}\nIMG_1.jpeg\nIMG_2.jpeg", None)
    assert decision is not None
    assert (decision.kind, decision.images) == (ShareKind.photo, [0, 2])
    assert decision.caption == NOTE


def test_photos_alone_have_no_text_even_when_shortcuts_names_them():
    decision = classify_share(
        [SharedFile("IMG_1.jpeg", JPEG), SharedFile("IMG_2.HEIC", JPEG)], "IMG_1.jpeg IMG_2", None
    )
    assert decision is not None and decision.caption is None and decision.images == [0, 1]


def test_the_note_text_may_come_as_a_text_file_only():
    files = [SharedFile("Notiz.txt", b"Omas", NOTE), SharedFile("IMG_1.jpeg", JPEG)]
    decision = classify_share(files, None, None)
    assert decision is not None and (decision.images, decision.caption) == ([1], NOTE)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"filename": "IMG.jpg", "head": b"\xff\xd8\xff\xe0 rest"}, (ShareKind.photo, "IMG.jpg")),
        ({"filename": "noname", "head": b"\x89PNG\r\n\x1a\nxx"}, (ShareKind.photo, "noname")),
        ({"filename": "a.bin", "head": b"RIFF\x00\x00\x00\x00WEBPVP8 "}, (ShareKind.photo, "a.bin")),
        ({"filename": "a.heic", "head": b"\x00\x00\x00\x18ftypheic"}, (ShareKind.photo, "a.heic")),
        ({"filename": "Eingabe", "head": b"%PDF-1.7\n"}, (ShareKind.pdf, "Eingabe.pdf")),
        ({"filename": "x.zip", "head": b"PK\x03\x04"}, (ShareKind.file, "x.zip")),
        ({"filename": "Rezept.TXT", "head": b"Kuchen"}, (ShareKind.file, "Rezept.TXT")),
        # a web page or web archive is ignored, the text and link decide
        ({"filename": "Seite.html", "head": b"<html>", "url": LINK}, (ShareKind.link, LINK)),
        ({"filename": "Seite.webarchive", "head": b"bplist00", "text": "Hallo"}, (ShareKind.text, "Hallo")),
        # a file beats text and link
        ({"filename": "a.pdf", "head": b"%PDF-", "text": "Hallo", "url": LINK}, (ShareKind.pdf, "a.pdf")),
        ({"url": LINK}, (ShareKind.link, LINK)),
        ({"url": LINK, "text": LINK}, (ShareKind.link, LINK)),
        ({"url": f"{LINK}\n{LINK}"}, (ShareKind.link, LINK)),
        ({"url": LINK, "text": "Schau mal: Griesspudding"}, (ShareKind.link, LINK)),
        ({"text": f"Schau mal: {LINK}."}, (ShareKind.link, LINK)),
        ({"url": LINK, "text": LONG}, (ShareKind.text, LONG.strip())),
        ({"text": LONG}, (ShareKind.text, LONG.strip())),
        ({"text": f"{LINK} {LINK}/2"}, (ShareKind.text, f"{LINK} {LINK}/2")),
        ({"url": f"{LINK}\nhttps://example.org/zwei"}, (ShareKind.link, LINK)),
        ({"url": "kein link"}, None),
        ({"url": "", "text": "  "}, None),
        ({}, None),
    ],
)
def test_decision_table(args: dict, expected):
    assert decide(**args) == expected


def post_share(api_client: TestClient, user: TestUser, *, file=None, **form):
    return api_client.post(f"{DRAFTS}/share", headers=user.token, data=form, files={"file": file} if file else None)


def only_draft(api_client: TestClient, user: TestUser, response) -> dict:
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["skipped"] == [] and len(body["created"]) == 1
    return api_client.get(f"{DRAFTS}/{body['created'][0]['id']}", headers=user.token).json()


def test_photo_with_a_wrong_name_is_a_photo_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft = only_draft(api_client, unique_user, post_share(api_client, unique_user, file=("Eingabe", png(40, 30))))
    assert draft["sourceType"] == "image" and draft["originalFiles"] == ["original-1.webp"]


def test_heic_photo_is_a_photo_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft = only_draft(api_client, unique_user, post_share(api_client, unique_user, file=("IMG.HEIC", heic(40, 30))))
    assert draft["sourceType"] == "image"


def test_pdf_without_suffix_is_read_as_pdf(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft = only_draft(
        api_client, unique_user, post_share(api_client, unique_user, file=("Eingabe", pdf_with_text(LINES)))
    )
    assert draft["sourceType"] == "text" and "Zeile 2" in draft["sourceText"]


def test_scanned_pdf_is_a_photo_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft = only_draft(api_client, unique_user, post_share(api_client, unique_user, file=("s.pdf", pdf_scan((50, 50)))))
    assert draft["sourceType"] == "image"


def test_zip_and_text_file_go_through_the_file_import(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    archive = zip_bytes({"a.txt": LONG.encode(), "b.txt": (LONG + " mehr").encode()})
    body = post_share(api_client, unique_user, file=("Eingabe", archive)).json()
    assert len(body["created"]) == 2
    draft = only_draft(api_client, unique_user, post_share(api_client, unique_user, file=("n.md", LONG.encode())))
    assert draft["sourceType"] == "text" and draft["sourceNote"] == "n.md"


def test_web_page_file_is_ignored_and_the_link_wins(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai):
    fake_page(None)
    fake_ai("recipe.json")
    response = post_share(api_client, unique_user, file=("Seite.html", b"<html>x</html>"), url=LINK, text=LINK)
    assert only_draft(api_client, unique_user, response)["sourceUrl"] == LINK


def test_list_of_links_takes_the_first(api_client: TestClient, unique_user: TestUser, fake_page, fake_ai):
    fake_page(None)
    fake_ai("recipe.json")
    response = post_share(api_client, unique_user, url=f"{LINK}\nhttps://example.org/zwei")
    assert only_draft(api_client, unique_user, response)["sourceUrl"] == LINK


def test_long_text_with_a_link_is_a_text_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    draft = only_draft(api_client, unique_user, post_share(api_client, unique_user, text=LONG, url=LINK))
    assert draft["sourceType"] == "text" and draft["sourceText"] == LONG.strip()


def test_nothing_usable_is_422(api_client: TestClient, unique_user: TestUser):
    response = post_share(api_client, unique_user, file=("Seite.webarchive", b"bplist00"), url="kein Link")
    assert response.status_code == 422 and response.json()["detail"] == {
        "code": "nothing_usable",
        "message": "Damit kann Kochheft nichts anfangen.",
    }
    assert response.json()["message"] == "Damit kann Kochheft nichts anfangen."  # D88: Siri reads this one


def test_video_link_is_never_fetched(api_client: TestClient, unique_user: TestUser):
    response = post_share(api_client, unique_user, url="https://www.youtube.com/watch?v=abc")
    assert response.status_code == 400 and response.json()["detail"] == {"code": "video_link"}
    assert "Videolinks" in response.json()["message"]


def test_too_large_photo_is_refused_like_the_images_route(api_client: TestClient, unique_user: TestUser, monkeypatch):
    monkeypatch.setattr(get_kh_settings(), "draft_max_image_mb", 1)
    response = post_share(api_client, unique_user, file=("a.png", png(1200, 1200, noise=True)))
    assert response.status_code == 400 and response.json()["detail"] == {"code": "too_large"}
    assert response.json()["message"] == "Die Datei ist zu groß."


def test_text_sent_also_as_txt_file_is_one_text_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    response = post_share(api_client, unique_user, file=("Eingabe.txt", LONG.encode()), text=LONG)
    draft = only_draft(api_client, unique_user, response)
    assert draft["sourceNote"] is None and draft["sourceText"] == LONG.strip()


def test_docx_like_zip_is_ignored(api_client: TestClient, unique_user: TestUser):
    docx = zip_bytes({"word/document.xml": b"<x/>", "a.png": png(40, 30)})
    response = post_share(api_client, unique_user, file=("Brief.docx", docx))
    assert response.status_code == 422 and response.json()["detail"]["code"] == "nothing_usable"


def test_share_with_no_draft_is_422_with_the_reason(api_client: TestClient, unique_user: TestUser):
    response = post_share(api_client, unique_user, file=("Eingabe.pdf", pdf_with_text(LINES, password="geheim")))
    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "nothing_created",
        "message": "Das hat nicht geklappt: PDF mit Passwort.",
    }
    assert response.json()["message"] == "Das hat nicht geklappt: PDF mit Passwort."


def test_needs_a_signed_in_user(api_client: TestClient):
    response = api_client.post(f"{DRAFTS}/share", data={"url": LINK})
    assert response.status_code == 401
    assert "angemeldet" in response.json()["message"]


def test_a_share_answers_with_a_sentence_for_siri(api_client: TestClient, unique_user: TestUser, fake_ai):
    body = post_share(api_client, unique_user, text=LONG).json()
    assert body["message"] == "Ist im Eingang: 1 Entwurf" and len(body["created"]) == 1


def test_the_confirmation_counts_in_the_plural():
    assert share_confirmation(3) == "Ist im Eingang: 3 Entwürfe"


def test_a_note_with_two_photos_is_one_draft_read_with_its_text(api_client: TestClient, unique_user: TestUser, fake_ai):
    """Shared from the Notes app: the shortcut sends every photo as a `file` field and the note's text as `text`."""
    calls = fake_ai("recipe.json")
    photos = [("file", ("IMG_1.jpeg", png(40, 30), "image/png")), ("file", ("IMG_2.jpeg", png(30, 40), "image/png"))]
    response = api_client.post(f"{DRAFTS}/share", headers=unique_user.token, data={"text": NOTE}, files=photos)
    draft = only_draft(api_client, unique_user, response)
    assert draft["sourceType"] == "image" and len(draft["originalFiles"]) == 2
    assert draft["sourceText"] == NOTE
    assert calls[-1]["content"] == NOTE and len(calls[-1]["images"]) == 2


def test_photos_beyond_the_limit_are_named_as_skipped(
    api_client: TestClient, unique_user: TestUser, fake_ai, monkeypatch
):
    fake_ai("recipe.json")
    monkeypatch.setattr(get_kh_settings(), "draft_max_images", 2)
    photos = [("file", (f"IMG_{n}.png", png(20 + n, 20), "image/png")) for n in range(3)]
    body = api_client.post(f"{DRAFTS}/share", headers=unique_user.token, files=photos).json()
    assert len(body["created"]) == 1 and len(body["created"][0]["originalFiles"]) == 2
    assert body["skipped"] == [{"name": "IMG_2.png", "reason": "too_many"}]
