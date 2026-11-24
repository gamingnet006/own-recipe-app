"""KH: what the tag suggestions send and receive."""

from pydantic import UUID4, Field

from mealie.schema._mealie import MealieModel


class TagRef(MealieModel):
    """A tag of the group as a recipe holds it."""

    id: UUID4
    name: str
    slug: str


class SuggestIn(MealieModel):
    """use_ai: also ask the AI about recipes the rules found nothing for (a few at a time)."""

    use_ai: bool = False


class TagProposal(MealieModel):
    """Tags proposed for one recipe that has none yet."""

    recipe_id: UUID4
    slug: str
    name: str
    tags: list[TagRef]


class SuggestOut(MealieModel):
    """The proposals, whether an AI provider is set, and how many tagless recipes have no proposal yet."""

    proposals: list[TagProposal]
    ai_available: bool
    without_proposal: int


class ApplyItem(MealieModel):
    """The tags a person confirmed for one recipe."""

    recipe_id: UUID4
    tag_ids: list[UUID4] = Field(min_length=1)


class ApplyIn(MealieModel):
    items: list[ApplyItem]
