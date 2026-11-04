"""KH: Küchenhelfer's switches from KH_* environment variables (kh/ops/.env). Mealie's own settings
stay untouched; the Mealie parts we hide stay off unless they are switched on here."""

from functools import lru_cache

from fastapi import HTTPException, status
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mealie.schema.response import ErrorResponse


class KhSettings(BaseSettings):
    """Switches and limits read from the environment, e.g. KH_SHARE_LINKS=true."""

    # env_ignore_empty: compose passes unset values as empty strings, which keep the defaults here
    model_config = SettingsConfigDict(env_prefix="KH_", env_ignore_empty=True)

    # Public recipe pages by link; Leitplanke 1: share links only on purpose, off by default
    share_links: bool = False

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


@lru_cache
def get_kh_settings() -> KhSettings:
    """The switches, read once like Mealie's get_app_settings()."""
    return KhSettings()


def require_share_links() -> None:
    """Route dependency: answers 404 while share links are off, as if the page did not exist."""
    if not get_kh_settings().share_links:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Share links are switched off"))
