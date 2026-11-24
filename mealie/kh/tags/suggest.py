"""KH: turns the rules' starter-tag keys into the group's own tags, for a draft in the review and for the proposals
on recipes that have no tags yet. Only tags the group already has are ever suggested, never new ones."""

from mealie.kh.tags.rules import suggested_keys
from mealie.kh.tags.schemas import TagRef
from mealie.kh.tags.starter import starter_key
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_organizers import TagDraft, TagOut


def rule_tags(recipe: RecipeDraft | RecipeOut, group_tags: list[TagOut]) -> list[TagRef]:
    """The group's tags the rules suggest for the recipe: those that are starter tags (in either language) whose
    key the rules gave; a family's renamed tag is not matched."""
    keys = suggested_keys(recipe)
    return [TagRef(id=tag.id, name=tag.name, slug=tag.slug) for tag in group_tags if starter_key(tag.name) in keys]


def add_rule_tags(recipe: RecipeDraft, group_tags: list[TagOut]) -> None:
    """Adds the rules' tags to a recognized draft next to the ones the AI already picked, without doubles."""
    have = {tag.id for tag in recipe.tags}
    recipe.tags += [
        TagDraft(id=t.id, name=t.name, slug=t.slug) for t in rule_tags(recipe, group_tags) if t.id not in have
    ]
