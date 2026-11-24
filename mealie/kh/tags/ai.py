"""KH: asks Mealie's own organizer step (the AI) which of the group's existing tags fit a saved recipe. It never
creates tags (create_new_organizers stays False) and sends only the recipe's name, description and texts."""

from mealie.kh.tags.schemas import TagRef
from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.services.openai import OpenAIService
from mealie.services.recipe.import_workflow.context import WorkflowContext, WorkflowInput, WorkflowOptions
from mealie.services.recipe.import_workflow.steps import ResolveOrganizersStep


def ai_available(repos: AllRepositories) -> bool:
    """Whether an AI provider is set."""
    return OpenAIService(repos).default_provider is not None


async def ai_tags(repos: AllRepositories, translator: Translator, recipe: RecipeOut) -> list[TagRef]:
    """The group's existing tags the AI picks for the recipe."""
    draft = RecipeDraft(
        name=recipe.name,
        description=recipe.description,
        recipe_ingredient=recipe.recipe_ingredient,
        recipe_instructions=recipe.recipe_instructions,
    )
    ctx = WorkflowContext(
        input=WorkflowInput(),
        options=WorkflowOptions(create_new_organizers=False),
        repos=repos,
        translator=translator,
        ai=OpenAIService(repos),
        draft_recipe=draft,
    )
    await ResolveOrganizersStep().run(ctx)
    return [TagRef(id=tag.id, name=tag.name, slug=tag.slug) for tag in draft.tags if tag.id]
