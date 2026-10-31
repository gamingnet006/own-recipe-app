"""KH: Küchenhelfer's switches from KH_* environment variables (kh/ops/.env). Mealie's own settings
stay untouched; the Mealie parts we hide stay off unless they are switched on here."""

from functools import lru_cache

from fastapi import HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict

from mealie.schema.response import ErrorResponse


class KhSettings(BaseSettings):
    """Switches read from the environment, e.g. KH_SHARE_LINKS=true."""

    model_config = SettingsConfigDict(env_prefix="KH_")

    # Public recipe pages by link; Leitplanke 1: share links only on purpose, off by default
    share_links: bool = False


@lru_cache
def get_kh_settings() -> KhSettings:
    """The switches, read once like Mealie's get_app_settings()."""
    return KhSettings()


def require_share_links() -> None:
    """Route dependency: answers 404 while share links are off, as if the page did not exist."""
    if not get_kh_settings().share_links:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Share links are switched off"))
