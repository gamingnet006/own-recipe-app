"""KH: video links (P7.2, D5): a link to a video site is never fetched; text or photos that come along make the
draft with the link as its source, without them the intake gets the code video_link."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from mealie.kh.drafts.recognize import VideoLinkError, build, error_code
from mealie.kh.drafts.video import is_video_link
from tests.kh.drafts.helpers import get_draft, open_ids, png, post_draft
from tests.utils.fixture_schemas import TestUser

REEL = "https://www.instagram.com/reel/abc123/"
TEXT = "Testkuchen: 200 g Mehl, 3 Eier."


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.instagram.com/reel/x", True),
        ("https://tiktok.com/@a/video/1", True),
        ("https://vm.tiktok.com/abc", True),
        ("https://m.youtube.com/watch?v=1", True),
        ("https://youtu.be/1", True),
        ("https://fb.watch/x", True),
        ("https://www.facebook.com/reel/1", True),
        ("youtube.com/watch?v=1", True),
        ("https://example.org/instagram.com", False),
        ("https://notyoutube.com/x", False),
        ("https://example.org/testkuchen", False),
    ],
)
def test_video_hosts_are_recognized_with_their_subdomains(url: str, expected: bool):
    assert is_video_link(url) is expected


def test_a_video_link_alone_is_refused_and_never_fetched(api_client: TestClient, unique_user: TestUser, fake_page):
    fake_page("page.html")
    before = open_ids(api_client, unique_user)
    response = post_draft(api_client, unique_user, data={"url": REEL})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "video_link"
    assert open_ids(api_client, unique_user) == before


def test_a_video_link_with_text_builds_the_draft_from_the_text(api_client: TestClient, unique_user: TestUser, fake_ai):
    calls = fake_ai("recipe.json")
    response = post_draft(api_client, unique_user, data={"url": REEL, "text": TEXT})
    assert response.status_code == 201
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["sourceType"] == "text"
    assert draft["sourceUrl"] == REEL
    assert calls == [{"content": TEXT, "translate_language": None}]


def test_a_video_link_with_a_photo_builds_the_draft_from_the_photo(
    api_client: TestClient, unique_user: TestUser, fake_ai
):
    fake_ai("recipe.json")
    files = [("images", ("shot.png", png(400, 300), "image/png"))]
    response = post_draft(api_client, unique_user, data={"url": REEL}, files=files)
    assert response.status_code == 201
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["sourceType"] == "image"
    assert draft["sourceUrl"] == REEL


def test_a_video_link_with_text_and_photo_is_still_several_sources(api_client: TestClient, unique_user: TestUser):
    files = [("images", ("shot.png", png(40, 30), "image/png"))]
    response = post_draft(api_client, unique_user, data={"url": REEL, "text": TEXT}, files=files)
    assert response.json()["detail"]["code"] == "several_sources"


def test_an_old_link_draft_to_a_video_site_fails_without_fetching(fake_page):
    fake_page("page.html")  # would give a recipe if the page were fetched
    draft = SimpleNamespace(source_type="link", source_url=REEL)
    with pytest.raises(VideoLinkError) as caught:
        asyncio.run(build(draft, None, None, None))  # type: ignore[arg-type]
    assert error_code(caught.value) == "video_link"
