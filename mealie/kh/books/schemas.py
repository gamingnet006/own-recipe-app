"""KH: what the book editor sends and keeps (D43), in camelCase like every Mealie answer. BookSettings is also the
shape of the JSON in kh_cookbook_print; recipes are named by slug."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from mealie.schema._mealie import MealieModel

BOOK_TEXT_MAX = 120  # longest title or subtitle

BookText = Annotated[str, StringConstraints(max_length=BOOK_TEXT_MAX)]


class BookRecipeSettings(MealieModel):
    """What the book does with one recipe; a recipe without an entry gets these defaults."""

    include: bool = True
    photo: bool = False
    servings: float | None = Field(None, gt=0)  # None: the recipe's own base amount


class BookSettings(MealieModel):
    """A cookbook's print settings; None for title or subtitle means the editor's default."""

    title: BookText | None = None
    subtitle: BookText | None = None
    title_page: bool = True
    toc: bool = True
    order: Literal["category", "alpha"] = "category"
    description: bool = True
    notes: bool = True
    oven: bool = True
    recipes: dict[str, BookRecipeSettings] = {}


class RecipeFlags(MealieModel):
    """A recipe's marks of ours."""

    own_photo: bool = False
