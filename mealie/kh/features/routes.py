"""KH: tells the frontend which hidden Mealie parts are switched on (GET /api/kh/features)."""

from fastapi import APIRouter

from mealie.kh.features.settings import get_kh_settings
from mealie.schema._mealie import MealieModel

router = APIRouter(prefix="/features")


class KhFeatures(MealieModel):
    """The switches the frontend needs, sent in camelCase like every Mealie answer."""

    share_links: bool


@router.get("", response_model=KhFeatures)
def get_features() -> KhFeatures:
    """Public, because the frontend loads it before anyone logs in; the switches hold no secrets."""
    return KhFeatures(share_links=get_kh_settings().share_links)
