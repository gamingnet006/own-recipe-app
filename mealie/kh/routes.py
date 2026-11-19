"""KH: Kochheft's routes under /api/kh. Mealie mounts this router once in mealie/routes/__init__.py;
each of our functions adds its routes here."""

from fastapi import APIRouter, Depends

from mealie.kh.accounts import routes as accounts
from mealie.kh.addons import routes as addons
from mealie.kh.addons.guards import require_addon
from mealie.kh.ai import routes as ai
from mealie.kh.allergens import routes as allergens
from mealie.kh.amounts import routes as amounts
from mealie.kh.books import routes as books
from mealie.kh.cooked import routes as cooked
from mealie.kh.drafts import routes as drafts
from mealie.kh.duplicates import routes as duplicates
from mealie.kh.features import routes as features
from mealie.kh.navigation import routes as navigation
from mealie.kh.notices import routes as notices
from mealie.kh.notifications import routes as notifications
from mealie.kh.nutrition import routes as nutrition
from mealie.kh.onboarding import routes as onboarding
from mealie.kh.shopping import routes as shopping
from mealie.kh.system import routes as system
from mealie.kh.weeksuggestion import routes as weeksuggestion
from mealie.kh.wishes import routes as wishes

router = APIRouter(prefix="/kh")

router.include_router(features.router, tags=["KH: Features"])
router.include_router(addons.router, tags=["KH: Add-ons"])
router.include_router(addons.admin_router, tags=["KH: Add-ons"])
router.include_router(accounts.router, tags=["KH: Accounts"])
router.include_router(accounts.admin_router, tags=["KH: Accounts"])
router.include_router(onboarding.router, tags=["KH: Onboarding"])
router.include_router(onboarding.public_router, tags=["KH: Onboarding"])
router.include_router(onboarding.admin_router, tags=["KH: Onboarding"])
router.include_router(onboarding.admin_tour_router, tags=["KH: Onboarding"])
router.include_router(drafts.router, tags=["KH: Drafts"])
router.include_router(drafts.origin_router, tags=["KH: Drafts"])
router.include_router(ai.router, tags=["KH: AI"])
router.include_router(navigation.router, tags=["KH: Navigation"])
router.include_router(notices.router, tags=["KH: Notices"])
router.include_router(notifications.router, tags=["KH: Notifications"])
router.include_router(amounts.router, tags=["KH: Amounts"])
router.include_router(cooked.router, tags=["KH: Cooked"])
router.include_router(books.router, tags=["KH: Books"], dependencies=[Depends(require_addon("books"))])
router.include_router(duplicates.router, tags=["KH: Duplicates"], dependencies=[Depends(require_addon("duplicates"))])
router.include_router(nutrition.router, tags=["KH: Nutrition"], dependencies=[Depends(require_addon("nutrition"))])
router.include_router(allergens.router, tags=["KH: Allergens"], dependencies=[Depends(require_addon("allergens"))])
router.include_router(shopping.router, tags=["KH: Shopping"], dependencies=[Depends(require_addon("shopping"))])
router.include_router(system.router, tags=["KH: System"])
router.include_router(wishes.router, tags=["KH: Wishes"], dependencies=[Depends(require_addon("planner"))])
router.include_router(
    weeksuggestion.router, tags=["KH: Week suggestion"], dependencies=[Depends(require_addon("planner"))]
)
