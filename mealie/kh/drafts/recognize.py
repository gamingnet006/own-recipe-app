"""KH: recognizing a draft in the background (phase 2): Mealie's web page reader for links, Mealie's AI for
text, images and links without recipe data. Runs after the response, with its own database session."""

from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import UUID4, ValidationError
from sqlalchemy.orm import Session

from mealie.core.exceptions import RateLimitError
from mealie.core.root_logger import get_logger
from mealie.db.db_setup import session_context
from mealie.kh.ai.chain import used_providers
from mealie.kh.ai.errors import AIUnavailableError
from mealie.kh.amounts.schemas import DraftAmounts
from mealie.kh.amounts.service import read_amounts
from mealie.kh.drafts.duplicates import candidates, find_duplicates
from mealie.kh.drafts.files import original_path
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import DraftError, DraftOut, DraftSource, DraftStatus
from mealie.kh.features.settings import get_kh_settings
from mealie.lang.providers import Translator
from mealie.pkgs.safehttp.transport import InvalidDomainError
from mealie.repos.all_repositories import get_repositories
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.household.household import HouseholdInDB
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.user.user import PrivateUser
from mealie.services.openai.openai import OpenAINotEnabledException, OpenAIService
from mealie.services.recipe.ai_recipe_service import AIProviderNotEnabledError, AIRecipeService
from mealie.services.recipe.import_workflow.exceptions import NoRecipeDataError
from mealie.services.scraper.scraper import create_from_html

logger = get_logger()

NO_AI = (OpenAINotEnabledException, AIProviderNotEnabledError)


def causes(ex: BaseException) -> list[BaseException]:
    """The exception and the ones it was raised from, as Mealie wraps errors it passes on."""
    chain: list[BaseException] = []
    current: BaseException | None = ex
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__
    return chain


def error_code(ex: Exception) -> DraftError:
    """Turns an exception from recognizing into the code the review shows."""
    if isinstance(ex, RateLimitError):
        return DraftError.quota_exceeded
    if any(isinstance(cause, AIUnavailableError) for cause in causes(ex)):
        return DraftError.ai_unavailable
    if isinstance(ex, NO_AI):
        return DraftError.ai_not_configured
    if isinstance(ex, NoRecipeDataError) or (isinstance(ex, HTTPException) and ex.status_code == 400):
        return DraftError.no_recipe_data
    if isinstance(ex, InvalidDomainError):
        return DraftError.address_blocked
    if isinstance(ex, ValidationError):
        return DraftError.invalid_result
    return DraftError.unknown


def set_fields(session: Session, draft_id: UUID4, **values: Any) -> None:
    """Changes a draft's columns directly; values must already be JSON-safe for the JSON columns."""
    session.execute(sa.update(KhDraft).where(KhDraft.id == draft_id).values(**values))
    session.commit()


def ai_model_used(repos: AllRepositories, *, images: bool) -> str | None:
    """Name and model of the provider Mealie's AI picks for this draft, as "<name> (<model>)"."""
    ai = OpenAIService(repos)
    provider = ai.image_provider if images else ai.default_provider
    return f"{provider.name} ({provider.model})" if provider else None


async def build(
    draft: DraftOut, ai: AIRecipeService, repos: AllRepositories, translator: Translator
) -> tuple[Recipe, bool]:
    """Recognizes the draft's source without saving a recipe; returns the recipe and whether the AI was used.
    What the AI reads comes out in the recipe language; a page's own recipe data stays as the page wrote it."""
    language = get_kh_settings().recipe_language or None
    if draft.source_type == DraftSource.link:
        url = draft.source_url or ""  # always set for links: create() refuses a link draft without one
        try:
            recipe, _ = await create_from_html(url, repos, translator)
            return recipe, False
        except HTTPException as ex:
            if ex.status_code != 400:  # 400: the page has no recipe data, the AI may still read it
                raise
        try:
            return await ai.build_recipe(url=url, translate_language=language), True
        except NO_AI as ex:
            raise NoRecipeDataError() from ex  # no recipe data on the page and no AI to read it
    if draft.source_type == DraftSource.text:
        return await ai.build_recipe(content=draft.source_text, translate_language=language), True
    images = [original_path(draft.id, name) for name in draft.original_files]
    return await ai.build_recipe(images=images, translate_language=language), True


async def recognize(draft_id: UUID4, *, user: PrivateUser, household: HouseholdInDB, translator: Translator) -> None:
    """Runs after the response: recognizes a working draft and stores the result as ready, with hints on
    possible duplicates, or the reason as failed."""
    with session_context() as session:
        repos = get_repositories(session, group_id=user.group_id, household_id=user.household_id)
        draft = drafts_repo(session, user.group_id, user.household_id).get_one(draft_id)
        if draft is None or draft.status != DraftStatus.working:
            return
        ai = AIRecipeService(repos, user, household, translator=translator)
        used_providers.set([])  # the priority list notes each provider that answers (D39)
        try:
            recipe, used_ai = await build(draft, ai, repos, translator)
            amounts = read_amounts(repos, recipe)  # German amounts, without AI (D39)
            recognized = recipe.model_dump(mode="json", by_alias=True)
            recognized["khAmounts"] = DraftAmounts(extras=amounts.extras).model_dump(mode="json", by_alias=True)
            warnings = find_duplicates(recognized, draft.source_url, candidates(repos, draft_id), get_kh_settings())
        except Exception as ex:
            session.rollback()  # on Postgres a failed statement aborts the transaction the failure is written in
            code = error_code(ex)
            if code == DraftError.unknown:
                logger.exception(f"KH: recognizing draft {draft_id} failed")
            else:
                logger.info(f"KH: recognizing draft {draft_id} failed: {code}")
            set_fields(session, draft_id, status=DraftStatus.failed, error=code, recipe=None, ai_model=None)
            return
        # the providers of the priority list that answered, in order (D39), else the one Mealie's settings name
        images = draft.source_type == DraftSource.image
        answered = ", ".join(used_providers.get() or [])
        ai_model = (answered or ai_model_used(repos, images=images)) if used_ai else None
        set_fields(
            session,
            draft_id,
            status=DraftStatus.ready,
            error=None,
            recipe=recognized,
            ai_model=ai_model,
            warnings=[warning.model_dump(mode="json", by_alias=True) for warning in warnings],
        )
