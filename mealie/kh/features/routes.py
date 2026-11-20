"""KH: tells the frontend which hidden Mealie parts are switched on (GET /api/kh/features)."""

from datetime import UTC, datetime

from fastapi import APIRouter

from mealie.core.config import get_app_dirs, get_app_settings
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.system.address import read_state, recent_change
from mealie.schema._mealie import MealieModel

router = APIRouter(prefix="/features")


class KhFeatures(MealieModel):
    """The switches the frontend needs, sent in camelCase like every Mealie answer."""

    share_links: bool
    notice_poll_minutes: int  # how often the bell asks for new notices (D39)
    source_url: str  # where the source of this fork can be read (AGPL), shown on the About page
    media: bool  # own audio and video files are accepted, because a Whisper server is set (P7.3)
    profile: str  # leicht, normal, stark or lokal (P7.4)
    clock_shortcut_url: str | None  # ready-made Clock timer shortcut to add, None while not configured (D42)
    import_shortcut_url: str | None  # ready-made share-sheet import shortcut, None while not configured (D68)
    siri_shortcut_url: str | None  # ready-made "Auf die Einkaufsliste" Siri shortcut, None while not configured (D68)
    email_ready: bool  # Mealie can send mail, so reset and welcome links work (D53)
    draft_max_text: int  # longest recipe text one draft takes; a text shared into the app is cut here (D57)
    base_url: str | None  # the address Mealie's BASE_URL names, None while it is still the default (D83)
    address_changed_at: str | None  # when the address last changed, while that is under 60 days ago (D85)


@router.get("", response_model=KhFeatures)
def get_features() -> KhFeatures:
    """Public, because the frontend loads it before anyone logs in; the switches hold no secrets."""
    settings, app_settings = get_kh_settings(), get_app_settings()
    changed = read_state(get_app_dirs().DATA_DIR)
    return KhFeatures(
        share_links=settings.share_links,
        notice_poll_minutes=settings.notice_poll_minutes,
        source_url=settings.source_url,
        media=bool(settings.whisper_url),
        profile=settings.profile,
        clock_shortcut_url=settings.clock_shortcut_url,
        import_shortcut_url=settings.import_shortcut_url,
        siri_shortcut_url=settings.siri_shortcut_url,
        email_ready=app_settings.SMTP_ENABLE,
        draft_max_text=settings.draft_max_text,
        base_url=None if app_settings.is_default_base_url else app_settings.BASE_URL,
        address_changed_at=changed.changed_at if changed and recent_change(changed, datetime.now(UTC)) else None,
    )
