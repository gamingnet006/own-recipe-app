"""KH: tag proposals for the household's recipes that have no tags, and applying only what a person confirmed."""

from fastapi import HTTPException, status

from mealie.kh.tags.ai import ai_available, ai_tags
from mealie.kh.tags.schemas import ApplyIn, SuggestOut, TagProposal
from mealie.kh.tags.suggest import rule_tags
from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_organizers import TagDraft
from mealie.services.openai.openai import OpenAINotEnabledException
from mealie.services.recipe.recipe_service import RecipeService

MAX_AI_RECIPES = 20  # recipes asked of the AI per run: every one is a request, free plans have quotas


async def suggest(repos: AllRepositories, translator: Translator, use_ai: bool) -> SuggestOut:
    """Proposals for recipes without tags: the rules first; with USE_AI the AI for a few recipes the rules gave
    nothing for. Nothing is saved."""
    group_tags = repos.tags.get_all()
    available = ai_available(repos)
    proposals: list[TagProposal] = []
    left = 0
    asked = 0
    for summary in repos.recipes.get_all():
        if summary.tags:
            continue
        recipe = repos.recipes.get_one(summary.slug, "slug")
        if recipe is None:
            continue
        found = rule_tags(recipe, group_tags)
        if not found and use_ai and available and asked < MAX_AI_RECIPES:
            asked += 1
            try:
                found = await ai_tags(repos, translator, recipe)
            except OpenAINotEnabledException:
                available = False
        if found:
            proposals.append(TagProposal(recipe_id=recipe.id, slug=recipe.slug, name=recipe.name or "", tags=found))
        else:
            left += 1
    return SuggestOut(proposals=proposals, ai_available=available, without_proposal=left)


def apply(repos: AllRepositories, recipes: RecipeService, data: ApplyIn) -> int:
    """Adds the confirmed tags to their recipes (keeping the tags a recipe has); returns how many recipes changed.
    A tag or recipe that does not belong to the group is a 404."""
    changed = 0
    for item in data.items:
        recipe = repos.recipes.get_one(item.recipe_id, "id")
        tags = [repos.tags.get_one(tag_id) for tag_id in item.tag_ids]
        if recipe is None or None in tags:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe or tag not found")
        merged = {tag.id: tag for tag in [*recipe.tags, *tags] if tag}
        draft = RecipeDraft(tags=[TagDraft(id=t.id, name=t.name, slug=t.slug) for t in merged.values()])
        recipes.patch_one(recipe.slug, draft)
        changed += 1
    return changed
