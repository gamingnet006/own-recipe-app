"""KH: the drafts service (phase 2): checks what comes in, keeps the household's drafts, retries failed
recognitions and marks recognitions that hang as interrupted."""

from datetime import timedelta
from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException, UploadFile, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.drafts.files import prepare_original, remove_draft_dir, store_original
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.recognize import set_fields
from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import DraftError, DraftOut, DraftSource, DraftStatus
from mealie.kh.features.settings import get_kh_settings
from mealie.lang.providers import Translator
from mealie.schema.household.household import HouseholdInDB
from mealie.schema.user.user import PrivateUser


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
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "not_found"})
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
