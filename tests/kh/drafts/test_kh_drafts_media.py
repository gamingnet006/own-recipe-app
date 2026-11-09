"""KH: own audio and video files (P7.3): with KH_WHISPER_URL a recording is transcribed by a Whisper server and the
transcript becomes the text of the draft. The Whisper server is a fake transport here, never a real one (D23)."""

import asyncio
import io
from collections.abc import Callable
from datetime import timedelta

import httpx
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts import recognize, whisper
from mealie.kh.drafts.files import draft_dir, drafts_root
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.features.settings import KhSettings, get_kh_settings
from tests.kh.drafts.helpers import get_draft, open_ids, png, post_draft
from tests.utils.fixture_schemas import TestUser

TRANSCRIPT = "Omas Apfelkuchen: 200 g Mehl, 3 Eier, 4 Äpfel."
AUDIO = ("media", ("omas-kuchen.m4a", b"not really audio", "audio/mp4"))

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def fake_whisper(monkeypatch: pytest.MonkeyPatch) -> Callable[[Handler | None], list[httpx.Request]]:
    """Switches Whisper on and answers its requests with HANDLER (default: the transcript); returns the requests."""

    def use(handler: Handler | None = None) -> list[httpx.Request]:
        seen: list[httpx.Request] = []

        def answer(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request) if handler else httpx.Response(200, json={"text": TRANSCRIPT})

        monkeypatch.setattr(get_kh_settings(), "whisper_url", "http://whisper:8000")
        monkeypatch.setattr(whisper, "TRANSPORT", httpx.MockTransport(answer))
        return seen

    return use


def test_a_recording_becomes_a_text_draft_with_its_file_name_as_note(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper
):
    calls = fake_ai("recipe.json")
    seen = fake_whisper()
    response = post_draft(api_client, unique_user, files=[AUDIO])
    assert response.status_code == 201
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert draft["sourceType"] == "text"
    assert draft["sourceText"] == TRANSCRIPT
    assert draft["sourceNote"] == "omas-kuchen.m4a"
    assert calls == [{"content": TRANSCRIPT, "translate_language": None}]
    request = seen[0]
    assert str(request.url) == "http://whisper:8000/v1/audio/transcriptions"
    assert b'name="language"\r\n\r\nde' in request.content
    assert b"Systran/faster-whisper-tiny" in request.content  # the default profile "leicht"
    assert not (draft_dir(draft["id"]) / whisper.MEDIA_FILE).exists()  # the recording is gone once transcribed


def test_a_recording_with_an_unknown_model_is_downloaded_once_and_asked_again(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper
):
    fake_ai("recipe.json")
    downloaded: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v1/models/"):
            downloaded.append(request.url.path)
            return httpx.Response(201)
        if not downloaded:
            return httpx.Response(404, json={"detail": "model not found"})
        return httpx.Response(200, json={"text": TRANSCRIPT})

    fake_whisper(handler)
    response = post_draft(api_client, unique_user, files=[AUDIO])
    assert get_draft(api_client, unique_user, response.json()["id"]).json()["status"] == "ready"
    assert downloaded == ["/v1/models/Systran/faster-whisper-tiny"]


def test_an_empty_transcript_is_no_recipe(api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper):
    calls = fake_ai("recipe.json")
    fake_whisper(lambda _: httpx.Response(200, json={"text": "  "}))
    response = post_draft(api_client, unique_user, files=[AUDIO])
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert (draft["status"], draft["error"]) == ("failed", "no_recipe_data")
    assert calls == []


def _raise(error: Exception) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    return handler


@pytest.mark.parametrize(
    ("handler", "code"),
    [
        (_raise(httpx.ConnectError("down")), "whisper_unreachable"),
        (_raise(httpx.ReadTimeout("slow")), "whisper_timeout"),
        (lambda _: httpx.Response(500, text="boom"), "whisper_failed"),
    ],
)
def test_whisper_problems_fail_the_draft_with_a_code_and_a_retry_works(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper, handler: Handler, code: str
):
    fake_ai("recipe.json")
    seen = fake_whisper(handler)
    response = post_draft(api_client, unique_user, files=[AUDIO])
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert (draft["status"], draft["error"]) == ("failed", code)
    assert (draft_dir(draft["id"]) / whisper.MEDIA_FILE).exists()  # kept for the retry

    seen.clear()
    fake_whisper()
    retried = api_client.post(f"/api/kh/drafts/{draft['id']}/retry", headers=unique_user.token)
    assert retried.status_code == 200
    assert get_draft(api_client, unique_user, draft["id"]).json()["status"] == "ready"


def test_a_too_big_recording_is_refused_and_leaves_no_draft(
    api_client: TestClient, unique_user: TestUser, fake_whisper, monkeypatch: pytest.MonkeyPatch
):
    seen = fake_whisper()
    monkeypatch.setattr(get_kh_settings(), "draft_max_media_mb", 1)
    before = open_ids(api_client, unique_user)
    big = ("media", ("big.mp3", b"x" * (1024 * 1024 + 1), "audio/mpeg"))
    response = post_draft(api_client, unique_user, files=[big])
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "media_too_large"
    assert open_ids(api_client, unique_user) == before
    assert seen == []


def test_without_whisper_the_file_is_refused(api_client: TestClient, unique_user: TestUser, monkeypatch):
    monkeypatch.setattr(get_kh_settings(), "whisper_url", None)
    response = post_draft(api_client, unique_user, files=[AUDIO])
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "media_not_configured"


def test_a_file_that_is_no_audio_or_video_is_refused(api_client: TestClient, unique_user: TestUser, fake_whisper):
    fake_whisper()
    photo = ("media", ("shot.png", png(40, 30), "image/png"))
    response = post_draft(api_client, unique_user, files=[photo])
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "not_audio_video"


def test_a_recording_with_a_text_is_several_sources(api_client: TestClient, unique_user: TestUser, fake_whisper):
    fake_whisper()
    response = post_draft(api_client, unique_user, data={"text": "Kuchen"}, files=[AUDIO])
    assert response.json()["detail"]["code"] == "several_sources"


def test_the_whisper_model_follows_the_profile_unless_set(monkeypatch: pytest.MonkeyPatch):
    for profile, model in (("leicht", "tiny"), ("normal", "base"), ("stark", "small"), ("lokal", "base")):
        assert whisper.whisper_model(KhSettings(profile=profile)) == f"Systran/faster-whisper-{model}"
    assert whisper.whisper_model(KhSettings(whisper_model="small")) == "Systran/faster-whisper-small"
    assert whisper.whisper_model(KhSettings(whisper_model="org/own-model")) == "org/own-model"


def test_features_tell_whether_recordings_are_accepted(api_client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_kh_settings(), "whisper_url", None)
    assert api_client.get("/api/kh/features").json()["media"] is False
    monkeypatch.setattr(get_kh_settings(), "whisper_url", "http://whisper:8000")
    assert api_client.get("/api/kh/features").json()["media"] is True


def _working_draft_with_recording(session: Session, user: TestUser, minutes_old: int) -> str:
    """A working recording draft whose last change was MINUTES_OLD minutes ago."""
    draft = drafts_repo(session, user.group_id, user.household_id).create(
        {
            "user_id": user.user_id,
            "status": "working",
            "source_type": "text",
            "source_note": "a.m4a",
            "group_id": user.group_id,
            "household_id": user.household_id,
        }
    )
    whisper.store_media(draft.id, io.BytesIO(b"audio"), 1)
    session.execute(
        sa.update(KhDraft)
        .where(KhDraft.id == draft.id)
        .values(update_at=get_utc_now() - timedelta(minutes=minutes_old))
    )
    session.commit()
    return str(draft.id)


def test_a_draft_with_its_recording_is_not_stale_while_whisper_may_still_work(
    api_client: TestClient, session: Session, unique_user: TestUser
):
    young = _working_draft_with_recording(session, unique_user, 20)  # over the stale minutes, under the read timeout
    old = _working_draft_with_recording(session, unique_user, 60)
    assert get_draft(api_client, unique_user, young).json()["status"] == "working"
    assert get_draft(api_client, unique_user, old).json()["error"] == "interrupted"


def test_transcribing_refreshes_the_drafts_clock(session: Session, unique_user: TestUser, fake_whisper):
    draft_id = _working_draft_with_recording(session, unique_user, 20)
    seen: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        session.expire_all()
        seen.append(session.get(KhDraft, draft_id).update_at)
        return httpx.Response(200, json={"text": TRANSCRIPT})

    fake_whisper(handler)
    draft = drafts_repo(session, unique_user.group_id, unique_user.household_id).get_one(draft_id)
    asyncio.run(recognize.transcribe_recording(draft, session))
    assert seen[0] > get_utc_now() - timedelta(minutes=1)


def test_a_duplicate_job_that_lost_the_recording_does_not_fail_the_draft(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper
):
    fake_ai("recipe.json")

    def handler(request: httpx.Request) -> httpx.Response:
        for recording in drafts_root().glob(f"*/{whisper.MEDIA_FILE}"):  # a second job finished first
            recording.unlink()
        return httpx.Response(200, json={"text": TRANSCRIPT})

    fake_whisper(handler)
    response = post_draft(api_client, unique_user, files=[AUDIO])
    assert get_draft(api_client, unique_user, response.json()["id"]).json()["status"] == "ready"


def test_a_job_whose_draft_was_marked_failed_meanwhile_does_not_overwrite_it(
    api_client: TestClient, session: Session, unique_user: TestUser, fake_ai, fake_whisper
):
    fake_ai("recipe.json")

    def handler(request: httpx.Request) -> httpx.Response:
        session.execute(
            sa.update(KhDraft).where(KhDraft.status == "working").values(status="failed", error="interrupted")
        )
        session.commit()
        return httpx.Response(200, json={"text": TRANSCRIPT})

    fake_whisper(handler)
    response = post_draft(api_client, unique_user, files=[AUDIO])
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert (draft["status"], draft["error"], draft["recipe"]) == ("failed", "interrupted", None)


def test_a_transcript_over_the_text_limit_is_cut_with_a_note(
    api_client: TestClient, unique_user: TestUser, fake_ai, fake_whisper, monkeypatch: pytest.MonkeyPatch
):
    fake_ai("recipe.json")
    monkeypatch.setattr(get_kh_settings(), "draft_max_text", 100)
    fake_whisper(lambda _: httpx.Response(200, json={"text": "x" * 500}))
    response = post_draft(api_client, unique_user, files=[AUDIO])
    draft = get_draft(api_client, unique_user, response.json()["id"]).json()
    assert draft["status"] == "ready"
    assert len(draft["sourceText"]) <= 100
    assert draft["sourceText"].endswith(recognize.TRUNCATED_NOTE)


def test_the_default_recording_limit_fits_cloudflares_upload_limit():
    assert KhSettings().draft_max_media_mb == 95
