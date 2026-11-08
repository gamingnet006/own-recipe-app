"""KH: Küchenhelfer's switches from KH_* environment variables (kh/ops/.env). Mealie's own settings
stay untouched; the Mealie parts we hide stay off unless they are switched on here."""

import re
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mealie.core.root_logger import get_logger
from mealie.schema.response import ErrorResponse

logger = get_logger()

# The only address the "add shortcut" button may open: a shared iOS Shortcut on iCloud
CLOCK_SHORTCUT_URL = re.compile(r"https://www\.icloud\.com/shortcuts/[A-Za-z0-9]+/?")


class KhSettings(BaseSettings):
    """Switches and limits read from the environment, e.g. KH_SHARE_LINKS=true."""

    # env_ignore_empty: compose passes unset values as empty strings, which keep the defaults here
    model_config = SettingsConfigDict(env_prefix="KH_", env_ignore_empty=True)

    # Public recipe pages by link; Leitplanke 1: share links only on purpose, off by default
    share_links: bool = False

    # Ready-made iOS Shortcut for the Clock timer (D42), an iCloud share link; anything else counts as unset
    clock_shortcut_url: str | None = None

    # Drafts (phase 2): what one draft may bring, and after how long a stuck recognition counts as interrupted
    draft_max_images: int = 5
    draft_max_image_mb: int = 20
    draft_max_text: int = 20000
    draft_stale_minutes: int = 15
    # Duplicate check: similarity from 0 to 1 from which a draft gets a hint
    duplicate_title: float = 0.85
    duplicate_ingredients: float = 0.7
    duplicate_title_with_ingredients: float = 0.5
    # Language every recipe the AI reads is translated into, as an English name like "German" (the way the AI
    # names a recipe's language, so Mealie skips recipes already in it); empty keeps the language they came in
    recipe_language: str = ""
    # AI priority list (D39): a 429 with a wait up to this many seconds is a short pause, not a used-up quota;
    # how long a provider is skipped when it names no wait (quota) or cannot be reached; a value out of bounds stops
    # the start with a message naming the setting
    ai_short_pause_seconds: int = Field(120, ge=0)
    ai_quota_pause_minutes: int = Field(60, ge=1)
    ai_down_pause_minutes: int = Field(10, ge=1)
    # Bell (D39): days a notice is kept, minutes between the app's checks for new ones
    notice_days: int = Field(30, ge=1)
    notice_poll_minutes: int = Field(5, ge=1)
    # About and system check (P8): the running image (its tag is the version), where the source can be read (AGPL),
    # the third-party notices shipped in the image, and the optional modules (only whether they are set is ever shown)
    image: str | None = None
    source_url: str = "https://github.com/gamingnet006/own-recipe-app"
    notices_file: Path = Path("/app/kh-docs/THIRD_PARTY_NOTICES.md")
    telegram_token: str | None = None
    # Telegram bot (P7.1): chats it listens to (comma list of chat IDs), the Mealie API token it hands drafts in
    # with, where Mealie is for it, and the address the family opens the app at (for the review link)
    telegram_allowed_ids: str = ""
    telegram_api_token: str | None = None
    telegram_mealie_url: str = "http://mealie:9000"
    base_url: str = "http://localhost:9091"
    whisper_url: str | None = None

    @field_validator("clock_shortcut_url")
    @classmethod
    def only_icloud_shortcut_links(cls, value: str | None) -> str | None:
        """Drops any address that is not an iCloud Shortcuts link; the warning names the setting, not the value."""
        if value is not None and not CLOCK_SHORTCUT_URL.fullmatch(value):
            logger.warning("KH_CLOCK_SHORTCUT_URL is not an iCloud Shortcuts link, ignored")
            return None
        return value


@lru_cache
def get_kh_settings() -> KhSettings:
    """The switches, read once like Mealie's get_app_settings()."""
    return KhSettings()


def require_share_links() -> None:
    """Route dependency: answers 404 while share links are off, as if the page did not exist."""
    if not get_kh_settings().share_links:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Share links are switched off"))
