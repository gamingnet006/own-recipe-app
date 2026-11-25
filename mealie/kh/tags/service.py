"""KH: tag proposals for the household's recipes that have no tags, and applying only what a person confirmed."""

from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.core.root_logger import get_logger
from mealie.kh.ai.errors import AIUnavailableError, QuotaUsedUpError
from mealie.kh.tags.ai import ai_available, ai_tags
from mealie.kh.tags.schemas import ApplyIn, SuggestIn, SuggestOut, TagProposal, TagRef
from mealie.kh.tags.suggest import rule_tags
from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.recipe.recipe_organizers import TagDraft
from mealie.services.openai.openai import OpenAINotEnabledException
from mealie.services.recipe.recipe_service import RecipeService

logger = get_logger()

MAX_AI_RECIPES = 10  # recipes asked of the AI per run: a request must stay well under the tunnel's 100 seconds


def _merged(first: list[TagRef], second: list[TagRef]) -> list[TagRef]:
    """FIRST followed by the tags of SECOND it does not have yet."""
    return first + [tag for tag in second if tag.id not in {own.id for own in first}]


async def _ask_ai(repos: AllRepositories, translator: Translator, recipe: RecipeOut) -> list[TagRef] | None:
    """The AI's tags for the recipe; None when no provider can answer or a quota is used up (then it is not asked
    again in this run); no tags when the answer for this one recipe failed, so it still counts as asked."""
    try:
        return await ai_tags(repos, translator, recipe)
    except (OpenAINotEnabledException, AIUnavailableError, QuotaUsedUpError):
        logger.info("KH: no AI provider answered for the tag suggestions")
        return None
    except Exception:  # an answer that cannot be used must not become a 500 that makes the page ask again
        logger.exception(f"KH: the AI's tags for recipe {recipe.id} could not be used")
        return []


async def suggest(repos: AllRepositories, translator: Translator, data: SuggestIn) -> SuggestOut:
    """Proposals for recipes without tags: the rules (time and diet) for all of them and, with use_ai, the AI for up
    to MAX_AI_RECIPES recipes not asked about before, merged with the rules' tags. Nothing is saved."""
    group_tags = repos.tags.get_all()
    available = ai_available(repos)
    skip = set(data.skip_ids)
    proposals: list[TagProposal] = []
    asked: list[UUID4] = []
    without = 0
    ai_left = 0
    for summary in repos.recipes.get_all():
        if summary.tags:
            continue
        recipe = repos.recipes.get_one(summary.slug, "slug")
        if recipe is None:
            continue
        found = rule_tags(recipe, group_tags)
        if data.use_ai and available and recipe.id not in skip and len(asked) < MAX_AI_RECIPES:
            asked.append(recipe.id)
            answer = await _ask_ai(repos, translator, recipe)
            available = answer is not None
            if answer is None:
                asked.pop()  # nobody answered: it stays open for a later try
            found = _merged(found, answer or [])
        if found:
            proposals.append(TagProposal(recipe_id=recipe.id, slug=recipe.slug, name=recipe.name or "", tags=found))
        else:
            without += 1
        if recipe.id not in skip and recipe.id not in asked:
            ai_left += 1
    return SuggestOut(
        proposals=proposals, ai_available=available, without_proposal=without, asked_ids=asked, ai_left=ai_left
    )


def apply(repos: AllRepositories, recipes: RecipeService, data: ApplyIn) -> int:
    """Adds the confirmed tags to their recipes (keeping the tags a recipe has); returns how many recipes changed.
    Every recipe and tag is looked up before the first one is changed, so an unknown one (404) saves nothing."""
    planned = []
    for item in data.items:
        recipe = repos.recipes.get_one(item.recipe_id, "id")
        tags = [repos.tags.get_one(tag_id) for tag_id in item.tag_ids]
        if recipe is None or None in tags:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipe or tag not found")
        merged = {tag.id: tag for tag in [*recipe.tags, *tags] if tag}
        planned.append((recipe.slug, [TagDraft(id=t.id, name=t.name, slug=t.slug) for t in merged.values()]))
    for slug, tags_draft in planned:
        recipes.patch_one(slug, RecipeDraft(tags=tags_draft))
    return len(planned)
