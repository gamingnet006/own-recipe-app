"""KH: Küchenhelfer's routes under /api/kh. Mealie mounts this router once in mealie/routes/__init__.py;
each of our functions adds its routes here."""

from fastapi import APIRouter

from mealie.kh.drafts import routes as drafts
from mealie.kh.features import routes as features

router = APIRouter(prefix="/kh")

router.include_router(features.router, tags=["KH: Features"])
router.include_router(drafts.router, tags=["KH: Drafts"])
router.include_router(drafts.origin_router, tags=["KH: Drafts"])
