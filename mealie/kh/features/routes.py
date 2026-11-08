"""KH: tells the frontend which hidden Mealie parts are switched on (GET /api/kh/features)."""

from fastapi import APIRouter

from mealie.kh.features.settings import get_kh_settings
from mealie.schema._mealie import MealieModel

router = APIRouter(prefix="/features")


class KhFeatures(MealieModel):
    """The switches the frontend needs, sent in camelCase like every Mealie answer."""

    share_links: bool
    notice_poll_minutes: int  # how often the bell asks for new notices (D39)
    source_url: str  # where the source of this fork can be read (AGPL), shown on the About page
    clock_shortcut_url: str | None  # ready-made Clock timer shortcut to add, None while not configured (D42)


@router.get("", response_model=KhFeatures)
def get_features() -> KhFeatures:
    """Public, because the frontend loads it before anyone logs in; the switches hold no secrets."""
    settings = get_kh_settings()
    return KhFeatures(
        share_links=settings.share_links,
        notice_poll_minutes=settings.notice_poll_minutes,
        source_url=settings.source_url,
        clock_shortcut_url=settings.clock_shortcut_url,
    )
