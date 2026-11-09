"""KH: starts the Telegram bot (`python -m mealie.kh.telegram`). Missing or unsuitable settings end the service
with a hint and exit code 0, so compose (restart: on-failure) does not start it again and again."""

import logging
import os
import re
import sys

from mealie.kh.features.settings import KhSettings, get_kh_settings
from mealie.kh.telegram.bot import Bot, Config

MB = 1024 * 1024
TOKEN_FORMAT = re.compile(r"\d+:[A-Za-z0-9_-]+")  # what @BotFather hands out; anything else is a typo


def config_from(settings: KhSettings) -> Config | str:
    """The bot's configuration, or the hint why it must not start."""
    if not settings.telegram_token:
        return "KH_TELEGRAM_TOKEN is not set (token from @BotFather): the Telegram bot stays off."
    if not TOKEN_FORMAT.fullmatch(settings.telegram_token):  # never echo it: it is a secret
        return "KH_TELEGRAM_TOKEN does not look like a bot token (digits, a colon, letters; no spaces): check it."
    if os.environ.get("KH_PROFILE") == "lokal":
        return "The profile 'lokal' keeps everything in the house: the Telegram bot does not start."
    try:
        allowed = frozenset(int(chat) for chat in settings.telegram_allowed_ids.split(",") if chat.strip())
    except ValueError:
        return "KH_TELEGRAM_ALLOWED_IDS must be a comma list of chat IDs, e.g. 123456789,987654321."
    if not allowed:
        return (
            "KH_TELEGRAM_ALLOWED_IDS is empty: set the chat IDs that may use the bot (write to it once to see yours)."
        )
    if not settings.telegram_api_token:
        return "KH_TELEGRAM_API_TOKEN is not set (Küchenhelfer: Profile > API Tokens): the Telegram bot stays off."
    return Config(
        token=settings.telegram_token,
        allowed_ids=allowed,
        api_token=settings.telegram_api_token,
        mealie_url=settings.telegram_mealie_url.rstrip("/"),
        base_url=settings.base_url.rstrip("/"),
        max_image_bytes=settings.draft_max_image_mb * MB,
    )


def main() -> int:
    """Runs the bot until the container stops."""
    config = config_from(get_kh_settings())
    if isinstance(config, str):
        sys.stderr.write(f"{config}\n")
        return 0
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("kh.telegram").info("Telegram bot started for %d chat(s)", len(config.allowed_ids))
    Bot(config).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
