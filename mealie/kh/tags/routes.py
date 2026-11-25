"""KH: the routes of the tag suggestions under /api/kh/tags: proposals for tagless recipes and applying the ones a
person confirmed. Needs the right to organize, like Mealie's own tag pages."""

from mealie.kh.tags import service
from mealie.kh.tags.schemas import ApplyIn, SuggestIn, SuggestOut
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.permissions import Perm, require
from mealie.routes._base.routers import UserAPIRouter
from mealie.services.recipe.recipe_service import RecipeService

router = UserAPIRouter(prefix="/tags")


@controller(router)
class KhTagsController(BaseUserController):
    """Suggestions for the household's recipes without tags."""

    @router.post("/suggest", response_model=SuggestOut, dependencies=[require(Perm.GROUP_ORGANIZE)])
    async def suggest(self, data: SuggestIn) -> SuggestOut:
        """Proposes tags (the group's existing ones) for recipes without any; saves nothing."""
        return await service.suggest(self.repos, self.translator, data)

    @router.post("/apply", dependencies=[require(Perm.GROUP_ORGANIZE)])
    def apply(self, data: ApplyIn) -> dict[str, int]:
        """Adds the confirmed tags to their recipes; answers how many recipes changed."""
        recipes = RecipeService(self.repos, self.user, self.household, translator=self.translator)
        return {"changed": service.apply(self.repos, recipes, data)}
