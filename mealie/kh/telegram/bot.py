"""KH: the Telegram bot's logic (P7.1): long polling, the allowed-chat check, turning messages into drafts and the
answers in the chat. All HTTP goes through one injectable transport, so tests need no network."""

import json
import logging
import re
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError

from mealie.kh.drafts.video import is_video_link
from mealie.kh.telegram.multipart import encode

logger = logging.getLogger("kh.telegram")

TELEGRAM = "https://api.telegram.org"
POLL_TIMEOUT_SECONDS = 50  # how long Telegram holds a getUpdates request open
REQUEST_TIMEOUT_SECONDS = POLL_TIMEOUT_SECONDS + 10
RETRY_DELAY_SECONDS = 30  # pause after a network error before polling again
MAX_RESPONSE_BYTES = 25 * 1024 * 1024  # more than Telegram lets a bot download

# What the user reads for the codes Mealie's drafts API answers with (the app has them in its own language files)
MEALIE_ERRORS = {
    "video_link": "Videos lädt Kochheft nicht herunter. Füge die Beschreibung ein oder lade einen Screenshot hoch.",
    "no_source": "Schick mir einen Link, einen Text oder ein Foto.",
    "several_sources": "Nur eins auf einmal: ein Link, ein Text oder ein Foto.",
    "too_many_images": "Zu viele Fotos auf einmal.",
    "too_large": "Das Foto ist zu groß.",
    "not_an_image": "Das ist kein Foto.",
    "text_too_long": "Der Text ist zu lang.",
}
UNKNOWN_CHAT = "Diese Chat-ID ist nicht freigeschaltet: {id}"
BAD_API_TOKEN = "Der API-Token des Bots ist ungültig. Leg in Kochheft unter Profil → API-Tokens einen neuen an."
BOT_OFF = (
    "Der Telegram-Bot ist in Kochheft ausgeschaltet. Ein Admin kann ihn unter Mehr → Zusatzfunktionen einschalten."
)
MEALIE_DOWN = "Kochheft ist gerade nicht erreichbar. Versuch es gleich noch einmal."
NOTHING_TO_USE = "Schick mir einen Link, einen Text oder ein Foto."

# the last character is not sentence punctuation or a closing bracket: "(link)." must give the link alone
URL = re.compile(r"https?://\S*[^\s.,;:!?)»]")

Transport = Callable[[urllib.request.Request, float], tuple[int, bytes]]


@dataclass(frozen=True)
class Config:
    """Everything the bot needs; filled from the KH_TELEGRAM_* settings by __main__."""

    token: str
    allowed_ids: frozenset[int]
    api_token: str
    mealie_url: str
    base_url: str
    max_image_bytes: int


class UserError(Exception):
    """A problem the chat should hear about; the text is the answer."""


def urllib_transport(request: urllib.request.Request, timeout: float) -> tuple[int, bytes]:
    """Sends the request; error statuses come back as answers, network errors raise OSError."""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - https and the Mealie URL only
            return response.status, response.read(MAX_RESPONSE_BYTES)
    except HTTPError as error:
        return error.code, error.read(MAX_RESPONSE_BYTES)


class Bot:
    """Polls Telegram and hands what the allowed chats send in as drafts."""

    def __init__(
        self, config: Config, transport: Transport = urllib_transport, sleep: Callable[[float], Any] = time.sleep
    ):
        self.config = config
        self.transport = transport
        self.sleep = sleep
        self.offset: int | None = None  # kept in memory: a restart may see the last messages again
        self.group_slug: str | None = None

    # --- Telegram ---

    def _telegram(self, method: str, **params: Any) -> Any:
        """Calls a Bot API method and returns its result."""
        request = urllib.request.Request(
            f"{TELEGRAM}/bot{self.config.token}/{method}",
            data=json.dumps(params).encode(),
            headers={"Content-Type": "application/json"},
        )
        status, body = self.transport(request, REQUEST_TIMEOUT_SECONDS)
        try:
            answer = json.loads(body)
        except ValueError:
            answer = {}
        if status != 200 or not answer.get("ok"):
            raise OSError(f"Telegram answered {method} with status {status}")
        return answer["result"]

    def _reply(self, chat_id: int, text: str) -> None:
        self._telegram("sendMessage", chat_id=chat_id, text=text)

    def _download_photo(self, sizes: list[dict[str, Any]]) -> bytes:
        """The largest size of a photo, refused above the image limit before and after the download."""
        largest = max(sizes, key=lambda size: size["width"] * size["height"])
        limit = self.config.max_image_bytes
        too_large = UserError(f"Das Foto ist zu groß (höchstens {limit // (1024 * 1024)} MB).")
        if largest.get("file_size", 0) > limit:
            raise too_large
        file = self._telegram("getFile", file_id=largest["file_id"])
        if file.get("file_size", 0) > limit:
            raise too_large
        request = urllib.request.Request(f"{TELEGRAM}/file/bot{self.config.token}/{file['file_path']}")
        status, data = self.transport(request, REQUEST_TIMEOUT_SECONDS)
        if status != 200:
            raise UserError("Das Foto konnte nicht von Telegram geladen werden.")
        if len(data) > limit:
            raise too_large
        return data

    # --- Mealie ---

    def _mealie(self, path: str, data: bytes | None = None, content_type: str | None = None) -> tuple[int, Any]:
        """Calls Mealie's API with the bot's token; the answer is parsed JSON (empty if it is none)."""
        headers = {"Authorization": f"Bearer {self.config.api_token}", "X-KH-Via": "telegram"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(f"{self.config.mealie_url}{path}", data=data, headers=headers)
        status, body = self.transport(request, REQUEST_TIMEOUT_SECONDS)
        try:
            return status, json.loads(body)
        except ValueError:
            return status, {}

    def _draft_link(self, draft_id: str) -> str:
        """The review page of a draft; empty if Mealie does not say which group the token belongs to."""
        if self.group_slug is None:
            status, me = self._mealie("/api/users/self")
            self.group_slug = me.get("groupSlug") if status == 200 else None
        return f": {self.config.base_url}/g/{self.group_slug}/drafts/{draft_id}" if self.group_slug else "."

    def _create_draft(self, fields: dict[str, str], images: list[bytes]) -> str:
        """Hands the source in and returns the answer for the chat."""
        body, content_type = encode(fields, images)
        status, answer = self._mealie("/api/kh/drafts", body, content_type)
        if status == 201:
            return f"Entwurf angelegt{self._draft_link(answer['id'])}"
        if status == 401:
            return BAD_API_TOKEN
        if status == 403:  # the Telegram add-on is off (D46)
            return BOT_OFF
        detail = answer.get("detail") if isinstance(answer, dict) else None
        code = detail.get("code") if isinstance(detail, dict) else None
        return MEALIE_ERRORS.get(str(code)) or f"Kochheft hat den Entwurf nicht angenommen (Fehler {status})."

    # --- Messages ---

    def _sources(self, message: dict[str, Any]) -> tuple[dict[str, str], list[bytes]]:
        """What the message hands in: a link, else its text, else its photo. A link to a video site goes along
        with the description or the photo, which then make the draft (the link only stays as its source)."""
        text = message.get("text") or message.get("caption") or ""
        link = (URL.search(text) or [None])[0]
        fields: dict[str, str] = {}
        images: list[bytes] = []
        if message.get("photo"):
            images.append(self._download_photo(message["photo"]))
            if link and is_video_link(link):
                fields["url"] = link
        elif link and not is_video_link(link):
            fields["url"] = link
        elif link:
            fields["url"] = link
            if description := text.replace(link, "").strip():
                fields["text"] = description
        elif text.strip():
            fields["text"] = text.strip()
        else:
            raise UserError(NOTHING_TO_USE)
        return fields, images

    def handle_message(self, message: dict[str, Any]) -> None:
        """Answers one message: its chat's ID if the chat is not allowed, else the draft or what went wrong."""
        chat_id = message["chat"]["id"]
        if chat_id not in self.config.allowed_ids:
            self._reply(chat_id, UNKNOWN_CHAT.format(id=chat_id))
            return
        try:
            answer = self._create_draft(*self._sources(message))
        except UserError as error:
            answer = str(error)
        except OSError as error:  # Mealie or Telegram's file server did not answer
            logger.warning("handing in failed: %s", type(error).__name__)  # never the error text: it may hold a URL
            answer = MEALIE_DOWN
        self._reply(chat_id, answer)

    # --- Loop ---

    def poll_once(self) -> None:
        """One long poll: handles the messages that came and moves the offset past them."""
        params: dict[str, Any] = {"timeout": POLL_TIMEOUT_SECONDS, "allowed_updates": ["message"]}
        if self.offset is not None:
            params["offset"] = self.offset
        for update in self._telegram("getUpdates", **params):
            self.offset = update["update_id"] + 1
            if "message" in update:
                try:
                    self.handle_message(update["message"])
                except (KeyError, TypeError, ValueError) as error:  # a message of a shape nobody expected
                    logger.warning("skipped a message: %s", type(error).__name__)

    def run(self, stop: Callable[[], bool] = lambda: False) -> None:
        """Polls until STOP says so; any error of a poll (network, cut-off or unreadable answer) only pauses for
        RETRY_DELAY_SECONDS. Only the error's type is logged: its text may hold the token in a URL."""
        while not stop():
            try:
                self.poll_once()
            except Exception as error:
                logger.warning("polling failed (%s), trying again in %s s", type(error).__name__, RETRY_DELAY_SECONDS)
                self.sleep(RETRY_DELAY_SECONDS)
