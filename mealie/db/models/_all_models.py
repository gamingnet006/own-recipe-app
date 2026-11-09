from .group import *
from .recipe import *
from .server import *
from .users import *

# KH: Küchenhelfer's own tables (phase 2), loaded after Mealie's so Alembic and the ORM know them
# isort: split
from mealie.kh.addons.models import KhHouseholdAddons  # noqa: F401
from mealie.kh.ai.models import KhAiProviderState  # noqa: F401
from mealie.kh.allergens.models import KhRecipeAllergen, KhSubstitution, KhUserAllergies  # noqa: F401
from mealie.kh.amounts.models import KhIngredientExtra, KhStepAmount  # noqa: F401
from mealie.kh.books.models import KhCookbookPrint, KhRecipeFlags  # noqa: F401
from mealie.kh.drafts.models import KhDraft  # noqa: F401
from mealie.kh.duplicates.models import KhDuplicateIgnored  # noqa: F401
from mealie.kh.notices.models import KhNotice, KhNoticeRead  # noqa: F401
from mealie.kh.nutrition.models import KhFoodNutrition  # noqa: F401
