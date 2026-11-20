"""KH: tests for reading PDFs (D84): a text layer becomes a text draft, a scan its embedded page images, and the
file import takes PDFs alone and inside a ZIP. The PDFs are generated here, never third-party files."""

import pytest
from fastapi.testclient import TestClient

from mealie.kh.drafts import pdf as pdf_module
from mealie.kh.drafts.pdf import PdfBudget, read_pdf
from mealie.kh.features.settings import get_kh_settings
from tests.kh.drafts.helpers import get_draft, pdf_scan, pdf_with_repeated_image, pdf_with_text, post_file, zip_bytes
from tests.utils.fixture_schemas import TestUser

LINES = [f"Zeile {n}: 200 g Mehl, 100 g Zucker, 3 Eier und eine Prise Salz verruehren" for n in range(5)]


def budget(settings=None) -> PdfBudget:
    return PdfBudget.from_settings(settings or get_kh_settings())


def test_text_layer_gives_its_text():
    text, images = read_pdf(pdf_with_text(LINES), get_kh_settings(), budget())
    assert "Zeile 0" in text and "Zeile 4" in text and images == []


def test_scan_gives_its_embedded_images_up_to_the_limit():
    settings = get_kh_settings().model_copy(update={"draft_max_images": 2})
    text, images = read_pdf(pdf_scan((60, 40), (60, 40), (60, 40)), settings, budget(settings))
    assert text == "" and len(images) == 2


def test_only_the_first_pages_are_read():
    settings = get_kh_settings().model_copy(update={"pdf_max_pages": 1})
    assert len(read_pdf(pdf_scan((60, 40), (60, 40)), settings, budget(settings))[1]) == 1


def test_little_text_counts_as_a_scan_with_a_note():
    # fewer than 200 letters: the page images are used instead (the text would be too thin to read a recipe from)
    with pytest.raises(ValueError, match="pdf_unreadable"):
        read_pdf(pdf_with_text(["Seite 1"]), get_kh_settings(), budget())


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (pdf_with_text(LINES, password="geheim"), "pdf_encrypted"),
        (b"%PDF-1.4 this is not a PDF", "unreadable"),
    ],
)
def test_encrypted_and_damaged_pdfs_are_named(data: bytes, reason: str):
    with pytest.raises(ValueError, match=reason):
        read_pdf(data, get_kh_settings(), budget())


def test_pdf_file_is_a_text_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    body = post_file(api_client, unique_user, "rezept.pdf", pdf_with_text(LINES)).json()
    assert body["skipped"] == [] and len(body["created"]) == 1
    draft = get_draft(api_client, unique_user, body["created"][0]["id"]).json()
    assert draft["sourceType"] == "text" and "Zeile 3" in draft["sourceText"] and draft["sourceNote"] == "rezept.pdf"


def test_scanned_pdf_file_is_one_photo_draft(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    body = post_file(api_client, unique_user, "scan.pdf", pdf_scan((80, 60), (80, 60))).json()
    draft = get_draft(api_client, unique_user, body["created"][0]["id"]).json()
    assert draft["sourceType"] == "image" and draft["originalFiles"] == ["original-1.webp", "original-2.webp"]


def test_pdfs_that_cannot_be_used_are_skipped_with_a_reason(api_client: TestClient, unique_user: TestUser, fake_ai):
    fake_ai("recipe.json")
    archive = zip_bytes(
        {
            "gut.pdf": pdf_with_text(LINES),
            "zu.pdf": pdf_with_text(LINES, password="geheim"),
            "kaputt.pdf": b"%PDF-1.4 kaputt",
            "leer.pdf": pdf_with_text([]),
        }
    )
    body = post_file(api_client, unique_user, "Buch.zip", archive).json()
    assert [draft["sourceNote"] for draft in body["created"]] == ["gut.pdf"]
    assert {item["name"]: item["reason"] for item in body["skipped"]} == {
        "zu.pdf": "pdf_encrypted",
        "kaputt.pdf": "unreadable",
        "leer.pdf": "pdf_unreadable",
    }


def test_a_page_listing_many_copies_of_one_image_stops_at_the_limit(monkeypatch: pytest.MonkeyPatch):
    settings = get_kh_settings().model_copy(update={"draft_max_images": 2})
    decoded = []
    real = pdf_module._jpeg
    monkeypatch.setattr(pdf_module, "_jpeg", lambda image: decoded.append(1) or real(image))
    _, images = read_pdf(pdf_with_repeated_image(2000), settings, budget(settings))
    assert len(images) == 2 and len(decoded) == 2


@pytest.mark.parametrize("mode", ["CMYK", "1", "L"])
def test_scans_in_other_colour_models_become_jpeg(mode: str):
    _, images = read_pdf(pdf_scan((60, 40), mode=mode), get_kh_settings(), budget())
    assert len(images) == 1 and images[0].startswith(b"\xff\xd8\xff")


def test_an_image_that_cannot_be_decoded_is_skipped_not_the_pdf(monkeypatch: pytest.MonkeyPatch):
    real = pdf_module._jpeg
    calls = []

    def flaky(image):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("broken image")
        return real(image)

    monkeypatch.setattr(pdf_module, "_jpeg", flaky)
    _, images = read_pdf(pdf_scan((60, 40), (60, 40)), get_kh_settings(), budget())
    assert len(images) == 1


def test_pdf_locked_with_an_empty_password_is_opened():
    text, _ = read_pdf(pdf_with_text(LINES, password=""), get_kh_settings(), budget())
    assert "Zeile 1" in text


def test_the_page_budget_is_shared_by_all_pdfs():
    settings = get_kh_settings().model_copy(update={"pdf_max_pages": 1})
    shared = budget(settings)
    assert read_pdf(pdf_scan((60, 40)), settings, shared)[1]
    with pytest.raises(ValueError, match="pdf_too_slow"):
        read_pdf(pdf_scan((60, 40)), settings, shared)


def test_time_limit_stops_reading_and_names_it(monkeypatch: pytest.MonkeyPatch):
    now = [0.0]
    monkeypatch.setattr(pdf_module, "monotonic", lambda: now[0])
    settings = get_kh_settings().model_copy(update={"pdf_max_seconds": 5})
    spent = budget(settings)
    now[0] = 6.0  # the clock runs past the deadline before the first page
    with pytest.raises(ValueError, match="pdf_too_slow"):
        read_pdf(pdf_scan((60, 40)), settings, spent)
