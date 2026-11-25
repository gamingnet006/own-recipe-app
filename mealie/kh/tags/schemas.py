"""KH: what the tag suggestions send and receive."""

from pydantic import UUID4, Field

from mealie.schema._mealie import MealieModel


class TagRef(MealieModel):
    """A tag of the group as a recipe holds it."""

    id: UUID4
    name: str
    slug: str


class SuggestIn(MealieModel):
    """use_ai: also ask the AI about tagless recipes (a few at a time); skip_ids: recipes already asked this visit,
    which are not asked again."""

    use_ai: bool = False
    skip_ids: list[UUID4] = Field(default_factory=list, max_length=1000)


class TagProposal(MealieModel):
    """Tags proposed for one recipe that has none yet."""

    recipe_id: UUID4
    slug: str
    name: str
    tags: list[TagRef]


class SuggestOut(MealieModel):
    """The proposals, whether an AI provider is set, how many tagless recipes have no proposal, which recipes the AI
    was asked about in this call and how many tagless recipes it has not been asked about yet."""

    proposals: list[TagProposal]
    ai_available: bool
    without_proposal: int
    asked_ids: list[UUID4]
    ai_left: int


class ApplyItem(MealieModel):
    """The tags a person confirmed for one recipe."""

    recipe_id: UUID4
    tag_ids: list[UUID4] = Field(min_length=1)


class ApplyIn(MealieModel):
    items: list[ApplyItem]
