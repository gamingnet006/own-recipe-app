"""KH: the family note of a recipe under /api/kh/recipes/{recipe_id}/note (D82), scoped to the user's household."""

from fastapi import Response, status
from pydantic import UUID4

from mealie.kh.notes import service
from mealie.kh.notes.schemas import NoteIn, NoteOut
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/recipes/{recipe_id}/note")


@controller(router)
class KhNotesController(BaseUserController):
    """Every person of a household sees and changes the household's note; other households' notes stay invisible."""

    @router.get("", response_model=NoteOut | None)
    def get_note(self, recipe_id: UUID4) -> NoteOut | None:
        """The household's note on the recipe, null when there is none."""
        return service.get_note(self.session, self.group_id, self.household_id, recipe_id)

    @router.put("", response_model=NoteOut | None)
    def put_note(self, recipe_id: UUID4, data: NoteIn) -> NoteOut | None:
        """Stores the note; an empty text deletes it and answers null."""
        return service.set_note(self.session, self.group_id, self.household_id, self.user.id, recipe_id, data.text)

    @router.delete("", status_code=status.HTTP_204_NO_CONTENT)
    def delete_note(self, recipe_id: UUID4) -> Response:
        """Deletes the note."""
        service.delete_note(self.session, self.group_id, self.household_id, recipe_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
