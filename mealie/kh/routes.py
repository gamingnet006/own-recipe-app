"""KH: Kochheft's routes under /api/kh. Mealie mounts this router once in mealie/routes/__init__.py;
each of our functions adds its routes here."""

from fastapi import APIRouter, Depends

from mealie.kh.addons import routes as addons
from mealie.kh.addons.guards import require_addon
from mealie.kh.ai import routes as ai
from mealie.kh.allergens import routes as allergens
from mealie.kh.amounts import routes as amounts
from mealie.kh.books import routes as books
from mealie.kh.drafts import routes as drafts
from mealie.kh.duplicates import routes as duplicates
from mealie.kh.features import routes as features
from mealie.kh.notices import routes as notices
from mealie.kh.nutrition import routes as nutrition
from mealie.kh.system import routes as system

router = APIRouter(prefix="/kh")

router.include_router(features.router, tags=["KH: Features"])
router.include_router(addons.router, tags=["KH: Add-ons"])
router.include_router(addons.admin_router, tags=["KH: Add-ons"])
router.include_router(drafts.router, tags=["KH: Drafts"])
router.include_router(drafts.origin_router, tags=["KH: Drafts"])
router.include_router(ai.router, tags=["KH: AI"])
router.include_router(notices.router, tags=["KH: Notices"])
router.include_router(amounts.router, tags=["KH: Amounts"])
router.include_router(books.router, tags=["KH: Books"], dependencies=[Depends(require_addon("books"))])
router.include_router(duplicates.router, tags=["KH: Duplicates"], dependencies=[Depends(require_addon("duplicates"))])
router.include_router(nutrition.router, tags=["KH: Nutrition"], dependencies=[Depends(require_addon("nutrition"))])
router.include_router(allergens.router, tags=["KH: Allergens"], dependencies=[Depends(require_addon("allergens"))])
router.include_router(system.router, tags=["KH: System"])
