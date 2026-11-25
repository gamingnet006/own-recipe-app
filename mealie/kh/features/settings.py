"""KH: Kochheft's switches from KH_* environment variables (kh/ops/.env). Mealie's own settings
stay untouched; the Mealie parts we hide stay off unless they are switched on here."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, status
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mealie.core.root_logger import get_logger
from mealie.schema.response import ErrorResponse

logger = get_logger()

# The only address the "add shortcut" buttons may open: a shared iOS Shortcut on iCloud
CLOCK_SHORTCUT_URL = re.compile(r"https://www\.icloud\.com/shortcuts/[A-Za-z0-9]+/?")
# The "Kochheft Timer" shortcut the maintainer shared (no personal data in it), so every install offers it unconfigured
DEFAULT_CLOCK_SHORTCUT_URL = "https://www.icloud.com/shortcuts/c6b533e1ee864389831f5a2d7801a9c9"
# The share-import, Siri and Clock shortcuts the maintainer shared (D42, D68, D84, D87); they ask for address and key
# when added and carry neither, so every install offers them unconfigured. The English ones ("..._en") are not shared
# yet: None, and the setup page then shows the manual English steps.
DEFAULT_SHORTCUT_URLS: dict[str, str | None] = {
    "clock_shortcut_url": DEFAULT_CLOCK_SHORTCUT_URL,
    "import_shortcut_url": "https://www.icloud.com/shortcuts/3fd264e8918848f7b1022edd57e2210c",
    "siri_shortcut_url": "https://www.icloud.com/shortcuts/28389dd5c63c42d2bfb983ba09201d04",
    "clock_shortcut_url_en": None,
    "import_shortcut_url_en": None,
    "siri_shortcut_url_en": None,
}

# Cloudflare's free plan cuts uploads at 100 MB, so a bigger recording could never reach the app through the tunnel
TUNNEL_UPLOAD_MB = 95


class KhSettings(BaseSettings):
    """Switches and limits read from the environment, e.g. KH_SHARE_LINKS=true."""

    # env_ignore_empty: compose passes unset values as empty strings, which keep the defaults here
    model_config = SettingsConfigDict(env_prefix="KH_", env_ignore_empty=True)

    # Public recipe pages by link; Leitplanke 1: share links only on purpose, off by default
    share_links: bool = False

    # Ready-made iOS Shortcuts (iCloud share links, shown on the setup page) for the Clock timer (D42), the share-sheet
    # import and "Hey Siri, Auf die Einkaufsliste" (D68), per language ("_en": English); empty keeps ours, anything
    # else unset (the page then shows the manual steps)
    clock_shortcut_url: str | None = DEFAULT_SHORTCUT_URLS["clock_shortcut_url"]
    import_shortcut_url: str | None = DEFAULT_SHORTCUT_URLS["import_shortcut_url"]
    siri_shortcut_url: str | None = DEFAULT_SHORTCUT_URLS["siri_shortcut_url"]
    clock_shortcut_url_en: str | None = None
    import_shortcut_url_en: str | None = None
    siri_shortcut_url_en: str | None = None

    # Drafts (phase 2): what one draft may bring, and after how long a stuck recognition counts as interrupted
    draft_max_images: int = 5
    draft_max_image_mb: int = 20
    draft_max_text: int = 20000
    draft_stale_minutes: int = 15
    # File import (D62): drafts one ZIP may create, and the size of an uploaded file and of a ZIP's unpacked content
    import_max_drafts: int = Field(100, ge=1)
    import_max_unzipped_mb: int = Field(50, ge=1)
    # PDF (D84): pages and seconds spent on reading PDFs
    pdf_max_pages: int = Field(20, ge=1)  # per request, shared by all PDFs in it
    pdf_max_seconds: int = Field(20, ge=1)  # per request
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
    # Accounts without e-mail (D53): hours the mailed welcome and confirm-e-mail links stay valid
    account_link_hours: int = Field(72, ge=1)
    # Seconds before the same person may ask for another confirmation mail (keeps the mail server from being flooded)
    verify_mail_cooldown_seconds: int = Field(60, ge=0)
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
    # Whisper (P7.3): the server for own recordings (none: no file field), its model (none: the profile's), and the
    # largest recording
    whisper_url: str | None = None
    whisper_model: str | None = None
    draft_max_media_mb: int = Field(TUNNEL_UPLOAD_MB, ge=1)
    # Profile (P7.4): how much the host can carry; sets the Whisper model, "lokal" keeps everything in the house
    profile: Literal["leicht", "normal", "stark", "lokal"] = "leicht"

    @field_validator(*DEFAULT_SHORTCUT_URLS)
    @classmethod
    def only_icloud_links_or_none(cls, value: str | None, info: ValidationInfo) -> str | None:
        """Empty keeps the built-in link; anything but an iCloud Shortcuts link is dropped (the warning names the
        setting, not the value)."""
        if value == "":
            return DEFAULT_SHORTCUT_URLS[str(info.field_name)]
        if value is not None and not CLOCK_SHORTCUT_URL.fullmatch(value):
            logger.warning(f"KH_{str(info.field_name).upper()} is not an iCloud Shortcuts link, ignored")
            return None
        return value

    def shortcut_urls(self) -> dict[str, dict[str, str | None]]:
        """The ready-made shortcut links per UI language, as the features answer sends them."""
        return {
            "de-DE": {
                "clock": self.clock_shortcut_url,
                "import": self.import_shortcut_url,
                "siri": self.siri_shortcut_url,
            },
            "en-US": {
                "clock": self.clock_shortcut_url_en,
                "import": self.import_shortcut_url_en,
                "siri": self.siri_shortcut_url_en,
            },
        }


@lru_cache
def get_kh_settings() -> KhSettings:
    """The switches, read once like Mealie's get_app_settings()."""
    return KhSettings()


def require_share_links() -> None:
    """Route dependency: answers 404 while share links are off, as if the page did not exist."""
    if not get_kh_settings().share_links:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Share links are switched off"))
