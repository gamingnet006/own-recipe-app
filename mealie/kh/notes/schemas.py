"""KH: the request and answer of a recipe's family note (D82)."""

from datetime import datetime

from pydantic import UUID4, Field

from mealie.schema._mealie import MealieModel, MealieOutModel

MAX_NOTE_LENGTH = 2000


class NoteIn(MealieModel):
    """The new text; empty (after trimming) deletes the note."""

    text: str = Field(max_length=MAX_NOTE_LENGTH)


class NoteOut(MealieOutModel):
    """The household's note on a recipe, who last changed it and when."""

    text: str
    updated_by: UUID4 | None  # None once that person's account is gone and nobody inherited
    updated_by_name: str
    updated_at: datetime | None = None
