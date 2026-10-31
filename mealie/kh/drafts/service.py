"""KH: the drafts service (phase 2): checks what comes in, keeps the household's drafts, retries failed
recognitions, marks recognitions that hang as interrupted, and turns an approved draft into a Mealie
recipe whose origin it then stays."""

from datetime import timedelta
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException, UploadFile, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts.duplicates import candidates, find_duplicates, normalize_url
from mealie.kh.drafts.files import (
    original_path,
    prepare_original,
    remove_draft_dir,
    remove_recognition_dir,
    store_original,
)
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.recognize import set_fields
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import (
    ApproveOut,
    DraftError,
    DraftOut,
    DraftSource,
    DraftStatus,
    DraftWarning,
    OriginOut,
)
from mealie.kh.features.settings import get_kh_settings
from mealie.lang.providers import Translator
from mealie.repos.all_repositories import get_repositories
from mealie.schema.household.household import HouseholdInDB
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.user.user import PrivateUser
from mealie.services.recipe.recipe_service import RecipeService


def bad_request(code: str) -> HTTPException:
    """400 with a code the intake page turns into a sentence."""
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail={"code": code})


def conflict(code: str, **extra: Any) -> HTTPException:
    """409 for an action the draft's state does not allow, with a code and optional details."""
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, **extra})


class DraftService:
    """The drafts of the user's household, with the checks the routes need."""

    def __init__(self, session: Session, user: PrivateUser, household: HouseholdInDB, translator: Translator):
        self.session = session
        self.user = user
        self.household = household
        self.translator = translator
        self.repo = drafts_repo(session, user.group_id, user.household_id)
        self.settings = get_kh_settings()

    def _source(self, url: str | None, text: str | None, images: list[UploadFile]) -> DraftSource:
        """The one source of a new draft; anything else is answered with 400 before something is stored."""
        given = [
            kind
            for kind, present in ((DraftSource.link, url), (DraftSource.text, text), (DraftSource.image, images))
            if present
        ]
        if not given:
            raise bad_request("no_source")
        if len(given) > 1:
            raise bad_request("several_sources")
        if len(images) > self.settings.draft_max_images:
            raise bad_request("too_many_images")
        if text and len(text) > self.settings.draft_max_text:
            raise bad_request("text_too_long")
        return given[0]

    def create(self, url: str | None, text: str | None, images: list[UploadFile]) -> DraftOut:
        """Stores a new draft as working, with its originals; the route starts the recognition."""
        url, text = (url or "").strip() or None, (text or "").strip() or None
        source = self._source(url, text, images)
        try:
            prepared = [prepare_original(upload.file.read(), self.settings.draft_max_image_mb) for upload in images]
        except ValueError as error:
            raise bad_request(str(error)) from error
        draft = self.repo.create(
            {
                "group_id": self.user.group_id,
                "household_id": self.user.household_id,
                "user_id": self.user.id,
                "status": DraftStatus.working,
                "source_type": source,
                "source_url": url,
                "source_url_normalized": normalize_url(url) if url else None,
                "source_text": text,
            }
        )
        if not prepared:
            return draft
        try:
            names = [store_original(draft.id, n, image) for n, image in enumerate(prepared, start=1)]
        except OSError:
            remove_draft_dir(draft.id)
            self.repo.delete(draft.id)
            raise
        set_fields(self.session, draft.id, original_files=names)
        return self.get(draft.id)

    def mark_stale(self) -> None:
        """Drafts that stayed working too long, e.g. after a restart mid-recognition, become failed."""
        cutoff = get_utc_now() - timedelta(minutes=self.settings.draft_stale_minutes)
        self.session.execute(
            sa.update(KhDraft)
            .where(
                KhDraft.group_id == self.user.group_id,
                KhDraft.household_id == self.user.household_id,
                KhDraft.status == DraftStatus.working,
                KhDraft.update_at < cutoff,
            )
            .values(status=DraftStatus.failed, error=DraftError.interrupted)
        )
        self.session.commit()

    def list_open(self) -> list[DraftOut]:
        """The household's drafts that are not approved yet, newest first."""
        self.mark_stale()
        query = (
            self.repo._query()
            .filter_by(**self.repo._filter_builder())
            .where(KhDraft.status != DraftStatus.approved)
            .order_by(KhDraft.created_at.desc())
        )
        return [DraftOut.model_validate(row) for row in self.session.execute(query).unique().scalars().all()]

    def get(self, draft_id: UUID4) -> DraftOut:
        """One draft of the household; 404 for any other, as if it did not exist."""
        self.mark_stale()
        draft = self.repo.get_one(draft_id)
        if draft is None:
            raise self._not_found()
        return draft

    def retry(self, draft_id: UUID4) -> DraftOut:
        """Sets a failed draft back to working; the route starts the recognition again."""
        draft = self.get(draft_id)
        if draft.status != DraftStatus.failed:
            raise conflict("not_failed")
        set_fields(
            self.session, draft_id, status=DraftStatus.working, error=None, recipe=None, ai_model=None, warnings=[]
        )
        return self.get(draft_id)

    def _not_found(self) -> HTTPException:
        """404, as if the draft or origin did not exist."""
        return HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "not_found"})

    def _already_approved(self, draft: DraftOut) -> HTTPException:
        """409 that also says where the saved recipe is."""
        recipe = self._all_repos().recipes.get_one(draft.recipe_id, "id") if draft.recipe_id else None
        return conflict("already_approved", slug=recipe.slug if recipe else None)

    def _all_repos(self):
        """Repositories that see every group, for checks that must not miss another household's recipe."""
        return get_repositories(self.session, group_id=None, household_id=None)

    def _household_repos(self):
        """Repositories of the user's household, as Mealie's own recipe routes use them."""
        return get_repositories(self.session, group_id=self.user.group_id, household_id=self.user.household_id)

    def _new_duplicates(self, draft: DraftOut) -> list[DraftWarning]:
        """Possible duplicates that turned up after the recognition, e.g. a recipe saved meanwhile."""
        known = {(warning.recipe_slug, warning.draft_id) for warning in draft.warnings}
        found = find_duplicates(
            draft.recipe or {}, draft.source_url, candidates(self._household_repos(), draft.id), self.settings
        )
        return [warning for warning in found if (warning.recipe_slug, warning.draft_id) not in known]

    def _save_recipe(self, draft: DraftOut) -> Recipe:
        """Saves the recognized recipe the way Mealie's import does; an image draft's first original
        becomes the cover, like in Mealie's create_from_ai."""
        recipes = RecipeService(self._household_repos(), self.user, self.household, self.translator)
        recipe = recipes.create_one(Recipe.model_validate(draft.recipe))
        if draft.source_type == DraftSource.image and draft.original_files:
            cover = original_path(draft.id, draft.original_files[0]).read_bytes()
            recipes.update_recipe_image(recipe.slug, cover, "webp")
        return recipe

    def approve(self, draft_id: UUID4, force: bool) -> ApproveOut:
        """Saves a ready draft as a Mealie recipe; anyone in the household may. Possible duplicates that are
        new since the recognition stop it unless FORCE. The claim on the draft is one conditional UPDATE, so
        of two people approving at once exactly one wins."""
        draft = self.get(draft_id)
        if draft.status == DraftStatus.approved:
            raise self._already_approved(draft)
        if draft.status != DraftStatus.ready:
            raise conflict("not_ready")
        if not force and (new := self._new_duplicates(draft)):
            raise conflict("duplicates", warnings=[warning.model_dump(mode="json", by_alias=True) for warning in new])
        claim = self.session.execute(
            sa.update(KhDraft)
            .where(KhDraft.id == draft_id, KhDraft.status == DraftStatus.ready)
            .values(status=DraftStatus.approved, approved_by=self.user.id, approved_at=get_utc_now())
        )
        self.session.commit()
        if claim.rowcount == 0:  # type: ignore[attr-defined]
            raise self._already_approved(self.get(draft_id))
        try:
            recipe = self._save_recipe(draft)
        except Exception:
            self.session.rollback()
            set_fields(self.session, draft_id, status=DraftStatus.ready, approved_by=None, approved_at=None)
            raise
        set_fields(self.session, draft_id, recipe_id=recipe.id)
        return ApproveOut(slug=recipe.slug)

    def discard(self, draft_id: UUID4) -> None:
        """Deletes a ready or failed draft with its originals and the image folder its recognition left."""
        draft = self.get(draft_id)
        if draft.status == DraftStatus.working:
            raise conflict("still_working")
        if draft.status == DraftStatus.approved:
            raise self._already_approved(draft)
        remove_recognition_dir((draft.recipe or {}).get("id"), self._all_repos())
        remove_draft_dir(draft.id)
        self.repo.delete(draft.id)

    def original_file(self, draft_id: UUID4, n: int) -> Path:
        """The n-th original (from 1) of a draft of the household."""
        draft = self.get(draft_id)
        if not 1 <= n <= len(draft.original_files):
            raise self._not_found()
        return original_path(draft.id, draft.original_files[n - 1])

    def origin(self, recipe_id: UUID4) -> OriginOut:
        """Where a recipe of the household came from; 404 for recipes without a draft."""
        found = self.repo.multi_query({"recipe_id": recipe_id}, limit=1)
        if not found:
            raise self._not_found()
        draft = found[0]
        return OriginOut(
            draft_id=draft.id,
            source_type=draft.source_type,
            source_url=draft.source_url,
            user_name=draft.user_name,
            created_at=draft.created_at,
            ai_model=draft.ai_model,
            original_count=len(draft.original_files),
        )
