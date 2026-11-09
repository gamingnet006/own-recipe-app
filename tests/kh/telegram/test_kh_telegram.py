"""KH: tests for the Telegram bot (P7.1) with a faked transport: no network, Telegram's answers are recorded
by hand, and for the end-to-end case Mealie's side is the real API through the test client."""

import json
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from email.parser import BytesParser
from email.policy import HTTP
from http.client import IncompleteRead
from urllib.error import URLError
from urllib.request import Request

import pytest
from fastapi.testclient import TestClient

from mealie.kh.features.settings import KhSettings
from mealie.kh.telegram.__main__ import config_from
from mealie.kh.telegram.bot import RETRY_DELAY_SECONDS, Bot, Config
from tests.utils.fixture_schemas import TestUser

TOKEN = "123456:SECRET-BOT-TOKEN"
API_TOKEN = "mealie-api-token"
MEALIE = "http://mealie:9000"
ALLOWED = 42
LINK = "https://example.org/testkuchen"
REEL = "https://www.instagram.com/reel/abc123/"


def make_config(**changes) -> Config:
    base = {
        "token": TOKEN,
        "allowed_ids": frozenset({ALLOWED}),
        "api_token": API_TOKEN,
        "mealie_url": MEALIE,
        "base_url": "https://kochbuch.example.org",
        "max_image_bytes": 1000,
    }
    return Config(**(base | changes))


class Fake:
    """Records every request and answers by the first route whose text is in the address."""

    def __init__(self) -> None:
        self.requests: list[Request] = []
        self.routes: list[tuple[str, Callable[[Request], tuple[int, bytes]]]] = []
        self.on("/sendMessage", lambda _: (200, json.dumps({"ok": True, "result": {}}).encode()))
        self.on("/api/users/self", lambda _: (200, json.dumps({"groupSlug": "home"}).encode()))

    def on(self, part: str, answer: Callable[[Request], tuple[int, bytes]]) -> None:
        self.routes.insert(0, (part, answer))

    def __call__(self, request: Request, timeout: float) -> tuple[int, bytes]:
        self.requests.append(request)
        for part, answer in self.routes:
            if part in request.full_url:
                return answer(request)
        raise AssertionError(f"unexpected request {request.full_url}")

    def to(self, part: str) -> list[Request]:
        return [r for r in self.requests if part in r.full_url]

    def replies(self) -> list[str]:
        return [json.loads(r.data)["text"] for r in self.to("/sendMessage")]  # type: ignore[arg-type]


def ok(result) -> tuple[int, bytes]:
    return 200, json.dumps({"ok": True, "result": result}).encode()


def mealie_answer(status: int, body: dict) -> Callable[[Request], tuple[int, bytes]]:
    return lambda _: (status, json.dumps(body).encode())


def message(text: str | None = None, chat: int = ALLOWED, **extra) -> dict:
    return {"chat": {"id": chat}, **({"text": text} if text else {}), **extra}


def parts(request: Request) -> dict[str, list[bytes]]:
    """The fields of a multipart request by name."""
    raw = b"Content-Type: " + request.get_header("Content-type").encode() + b"\r\n\r\n" + request.data  # type: ignore[operator]
    found: dict[str, list[bytes]] = {}
    for part in BytesParser(policy=HTTP).parsebytes(raw).iter_parts():
        found.setdefault(part.get_param("name", header="content-disposition"), []).append(part.get_payload(decode=True))
    return found


@pytest.fixture
def fake() -> Fake:
    fake = Fake()
    fake.on("/api/kh/drafts", mealie_answer(201, {"id": "d1"}))
    return fake


def bot_with(fake: Fake, **changes) -> Bot:
    return Bot(make_config(**changes), fake, sleep=lambda _: None)


def test_a_link_becomes_a_draft_and_the_chat_gets_the_review_link(fake: Fake):
    bot_with(fake).handle_message(message(LINK))
    request = fake.to("/api/kh/drafts")[0]
    assert request.get_header("Authorization") == f"Bearer {API_TOKEN}"
    assert request.full_url == f"{MEALIE}/api/kh/drafts"
    assert parts(request) == {"url": [LINK.encode()]}
    assert fake.replies() == ["Entwurf angelegt: https://kochbuch.example.org/g/home/drafts/d1"]


def test_a_text_becomes_a_draft(fake: Fake):
    bot_with(fake).handle_message(message("Testkuchen: 200 g Mehl, 3 Eier."))
    assert parts(fake.to("/api/kh/drafts")[0]) == {"text": [b"Testkuchen: 200 g Mehl, 3 Eier."]}


def test_a_link_inside_a_text_is_the_source(fake: Fake):
    bot_with(fake).handle_message(message(f"Schau mal {LINK} lecker"))
    assert parts(fake.to("/api/kh/drafts")[0]) == {"url": [LINK.encode()]}


def test_a_video_link_with_a_description_sends_both(fake: Fake):
    bot_with(fake).handle_message(message(f"{REEL}\nTestkuchen: 200 g Mehl."))
    assert parts(fake.to("/api/kh/drafts")[0]) == {"url": [REEL.encode()], "text": [b"Testkuchen: 200 g Mehl."]}


def test_a_video_link_alone_gets_the_readable_answer_of_mealie(fake: Fake):
    fake.on("/api/kh/drafts", mealie_answer(400, {"detail": {"code": "video_link"}}))
    bot_with(fake).handle_message(message(REEL))
    assert fake.replies() == [
        "Videos lädt Küchenhelfer nicht herunter. Füge die Beschreibung ein oder lade einen Screenshot hoch."
    ]


def test_the_largest_photo_is_downloaded_and_sent_as_an_image(fake: Fake):
    fake.on("/getFile", lambda r: ok({"file_path": "photos/big.jpg", "file_size": 300}))
    fake.on("/file/bot", lambda r: (200, b"JPEGDATA"))
    sizes = [
        {"file_id": "small", "width": 90, "height": 60, "file_size": 100},
        {"file_id": "big", "width": 1280, "height": 960, "file_size": 300},
    ]
    bot_with(fake).handle_message(message(photo=sizes))
    assert json.loads(fake.to("/getFile")[0].data)["file_id"] == "big"
    assert fake.to("/file/bot")[0].full_url == f"https://api.telegram.org/file/bot{TOKEN}/photos/big.jpg"
    assert parts(fake.to("/api/kh/drafts")[0]) == {"images": [b"JPEGDATA"]}


def test_a_photo_above_the_limit_is_refused_before_it_is_downloaded(fake: Fake):
    photo = [{"file_id": "big", "width": 4000, "height": 3000, "file_size": 5000}]
    bot_with(fake).handle_message(message(photo=photo))
    assert fake.to("/getFile") == [] and fake.to("/api/kh/drafts") == []
    assert "zu groß" in fake.replies()[0]


def test_a_photo_that_turns_out_larger_than_announced_is_refused(fake: Fake):
    fake.on("/getFile", lambda r: ok({"file_path": "p.jpg", "file_size": 10}))
    fake.on("/file/bot", lambda r: (200, b"x" * 2000))
    bot_with(fake).handle_message(message(photo=[{"file_id": "a", "width": 1, "height": 1}]))
    assert fake.to("/api/kh/drafts") == []
    assert "zu groß" in fake.replies()[0]


def test_an_unknown_chat_only_gets_its_id(fake: Fake):
    bot_with(fake).handle_message(message(LINK, chat=777))
    assert fake.replies() == ["Diese Chat-ID ist nicht freigeschaltet: 777"]
    assert fake.to("/api/kh/drafts") == []


def test_a_mealie_error_is_answered_readably_and_a_bad_token_too(fake: Fake):
    fake.on("/api/kh/drafts", mealie_answer(400, {"detail": {"code": "text_too_long"}}))
    bot = bot_with(fake)
    bot.handle_message(message("x"))
    fake.on("/api/kh/drafts", mealie_answer(401, {"detail": "Unauthorized"}))
    bot.handle_message(message("x"))
    fake.on("/api/kh/drafts", mealie_answer(500, {}))
    bot.handle_message(message("x"))
    assert fake.replies() == [
        "Der Text ist zu lang.",
        "Der API-Token des Bots ist ungültig. Leg in Küchenhelfer unter Profil → API-Tokens einen neuen an.",
        "Küchenhelfer hat den Entwurf nicht angenommen (Fehler 500).",
    ]


def test_a_switched_off_bot_says_so_and_announces_itself_to_mealie(fake: Fake):
    fake.on("/api/kh/drafts", mealie_answer(403, {"detail": {"message": "Telegram-Bot ist ausgeschaltet."}}))
    bot_with(fake).handle_message(message("x"))
    assert fake.replies() == [
        "Der Telegram-Bot ist in Küchenhelfer ausgeschaltet. Ein Admin kann ihn unter Mehr → Zusatzfunktionen "
        "einschalten."
    ]
    assert fake.to("/api/kh/drafts")[0].get_header("X-kh-via") == "telegram"


def test_an_unreachable_mealie_is_answered(fake: Fake):
    def down(request: Request):
        raise URLError("refused")

    fake.on("/api/kh/drafts", down)
    bot_with(fake).handle_message(message(LINK))
    assert fake.replies() == ["Küchenhelfer ist gerade nicht erreichbar. Versuch es gleich noch einmal."]


def test_a_message_without_content_is_answered_with_a_hint(fake: Fake):
    bot_with(fake).handle_message(message())
    assert "Link" in fake.replies()[0]


def test_polling_keeps_the_offset_and_handles_each_update(fake: Fake):
    updates = [{"update_id": 10, "message": message(LINK)}, {"update_id": 11, "edited_message": {}}]
    fake.on("/getUpdates", lambda r: ok(updates))
    bot = bot_with(fake)
    bot.poll_once()
    bot.poll_once()
    polls = [json.loads(r.data) for r in fake.to("/getUpdates")]
    assert polls[0] == {"timeout": 50, "allowed_updates": ["message"]}
    assert polls[1]["offset"] == 12
    assert len(fake.to("/api/kh/drafts")) == 2


def test_a_network_error_backs_off_and_polling_goes_on(fake: Fake, caplog: pytest.LogCaptureFixture):
    answers = iter([URLError(f"cannot reach {TOKEN}"), ok([])])

    def getUpdates(request: Request):
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    fake.on("/getUpdates", getUpdates)
    pauses: list[float] = []
    bot = Bot(make_config(), fake, sleep=pauses.append)
    stops = iter([False, False, True])
    with caplog.at_level(logging.DEBUG):
        bot.run(stop=lambda: next(stops))
    assert pauses == [RETRY_DELAY_SECONDS]
    assert TOKEN not in caplog.text and TOKEN not in str(pauses)


@pytest.mark.parametrize("error", [IncompleteRead(b"part"), ValueError(f"bad json after {TOKEN}")])
def test_any_error_of_a_poll_backs_off_and_logs_only_its_type(
    fake: Fake, caplog: pytest.LogCaptureFixture, error: Exception
):
    answers = iter([error, ok([])])

    def getUpdates(request: Request):
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    fake.on("/getUpdates", getUpdates)
    pauses: list[float] = []
    stops = iter([False, False, True])
    with caplog.at_level(logging.DEBUG):
        Bot(make_config(), fake, sleep=pauses.append).run(stop=lambda: next(stops))
    assert pauses == [RETRY_DELAY_SECONDS]
    assert type(error).__name__ in caplog.text and TOKEN not in caplog.text


def test_a_token_of_the_wrong_shape_is_refused_without_printing_it():
    for bad in ("123456: SECRET", "123456:SECRET\n", "no-colon", ":abc"):
        hint = config_from(KhSettings(telegram_token=bad, telegram_allowed_ids="1", telegram_api_token="x"))
        assert isinstance(hint, str) and "KH_TELEGRAM_TOKEN" in hint and "SECRET" not in hint and bad not in hint
    assert isinstance(
        config_from(KhSettings(telegram_token=TOKEN, telegram_allowed_ids="1", telegram_api_token="x")), Config
    )


def run_main(**env: str) -> subprocess.CompletedProcess:
    """python -m mealie.kh.telegram with only the given KH_ settings."""
    clean = {k: v for k, v in os.environ.items() if not k.startswith("KH_")}
    return subprocess.run(
        [sys.executable, "-m", "mealie.kh.telegram"], env=clean | env, capture_output=True, text=True, timeout=60
    )


def test_without_a_token_the_service_exits_with_a_hint():
    done = run_main()
    assert done.returncode == 0
    assert "KH_TELEGRAM_TOKEN" in done.stderr


def test_the_lokal_profile_refuses_to_start():
    done = run_main(KH_TELEGRAM_TOKEN=TOKEN, KH_PROFILE="lokal")
    assert done.returncode == 0
    assert "lokal" in done.stderr and TOKEN not in done.stderr + done.stdout


def test_without_allowed_chats_or_api_token_the_service_exits_with_a_hint():
    done = run_main(KH_TELEGRAM_TOKEN=TOKEN)
    assert done.returncode == 0
    assert "KH_TELEGRAM_ALLOWED_IDS" in done.stderr
    done = run_main(KH_TELEGRAM_TOKEN=TOKEN, KH_TELEGRAM_ALLOWED_IDS="1, 2")
    assert "KH_TELEGRAM_API_TOKEN" in done.stderr
    done = run_main(KH_TELEGRAM_TOKEN=TOKEN, KH_TELEGRAM_ALLOWED_IDS="anna")
    assert "comma list" in done.stderr


def test_a_message_of_an_unexpected_shape_does_not_stop_the_polling(fake: Fake):
    fake.on(
        "/getUpdates",
        lambda r: ok([{"update_id": 1, "message": {"no": "chat"}}, {"update_id": 2, "message": message(LINK)}]),
    )
    bot = bot_with(fake)
    bot.poll_once()
    assert bot.offset == 3 and len(fake.to("/api/kh/drafts")) == 1


def test_the_end_to_end_multipart_is_accepted_by_the_real_drafts_api(api_client: TestClient, unique_user: TestUser):
    """Link with description and a photo, as the bot sends them, against Mealie itself."""
    token = unique_user.token["Authorization"].removeprefix("Bearer ")
    fake = Fake()

    def to_mealie(request: Request) -> tuple[int, bytes]:
        path = request.full_url.removeprefix(MEALIE)
        headers = {k: v for k, v in request.header_items() if k.lower() in ("authorization", "content-type")}
        if request.data is None:
            response = api_client.get(path, headers=headers)
        else:
            response = api_client.post(path, content=request.data, headers=headers)
        return response.status_code, response.content

    fake.on("/api/", to_mealie)
    bot = Bot(make_config(api_token=token, max_image_bytes=10**7), fake, sleep=lambda _: None)
    bot.handle_message(message(f"{REEL}\nTestkuchen: 200 g Mehl, 3 Eier."))
    assert fake.replies()[0].startswith("Entwurf angelegt: https://kochbuch.example.org/g/")
    draft_id = fake.replies()[0].rsplit("/", 1)[1]
    draft = api_client.get(f"/api/kh/drafts/{draft_id}", headers=unique_user.token).json()
    assert draft["sourceType"] == "text" and draft["sourceUrl"] == REEL
