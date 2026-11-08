"""KH: what the duplicate report sends and takes (D43), in camelCase like every Mealie answer."""

from mealie.schema._mealie import MealieModel

DUPLICATE_REPORT_LIMIT = 200  # most pairs one report lists


class RecipeRef(MealieModel):
    """A recipe in a pair: enough to show where it came from and to open or delete it."""

    slug: str
    name: str
    org_url: str | None = None
    tags: list[str]  # tag names


class DuplicatePair(MealieModel):
    """Two recipes that may be the same dish; kind is the reason, similarity from 0 to 1 how alike the titles are."""

    a: RecipeRef
    b: RecipeRef
    kind: str
    similarity: float


class IgnorePair(MealieModel):
    """Two recipe slugs the family wants to keep both of."""

    a: str
    b: str
