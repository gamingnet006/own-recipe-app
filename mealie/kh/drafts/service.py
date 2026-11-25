"""KH: the drafts service (phase 2): checks what comes in, keeps the household's drafts, retries failed
recognitions, marks recognitions that hang as interrupted, and turns an approved draft into a Mealie
recipe whose origin it then stays."""

from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException, UploadFile, status
from PIL import Image
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.amounts.schemas import DraftAmounts
from mealie.kh.amounts.service import save_amounts
from mealie.kh.drafts.duplicates import candidates, find_duplicates, normalize_url
from mealie.kh.drafts.edit import edit_ingredient, edit_name, edit_step
from mealie.kh.drafts.file_import import read_file
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
    ApproveIn,
    ApproveOut,
    DraftEditIn,
    DraftError,
    DraftOut,
    DraftSource,
    DraftStatus,
    DraftWarning,
    FileImportOut,
    OriginOut,
    SkippedFile,
)
from mealie.kh.drafts.share import ShareDecision, ShareKind
from mealie.kh.drafts.video import is_video_link
from mealie.kh.drafts.whisper import RECORDING_STALE_AFTER, media_path, store_media
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.i18n.locale import DEFAULT_LOCALE
from mealie.lang.providers import Translator
from mealie.repos.all_repositories import get_repositories
from mealie.schema.household.household import HouseholdOut
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut
from mealie.schema.user.user import PrivateUser
from mealie.services.parser_services._base import DataMatcher
from mealie.services.recipe.recipe_service import RecipeService

MAX_NOTE = 200  # longest file name kept as a draft's note


def bad_request(code: str) -> HTTPException:
    """400 with a code the intake page turns into a sentence."""
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail={"code": code})


def conflict(code: str, **extra: Any) -> HTTPException:
    """409 for an action the draft's state does not allow, with a code and optional details."""
    return HTTPException(status.HTTP_409_CONFLICT, detail={"code": code, **extra})


class DraftService:
    """The drafts of the user's household, with the checks the routes need."""

    def __init__(self, session: Session, user: PrivateUser, household: HouseholdOut, translator: Translator):
        self.session = session
        self.user = user
        self.household = household
        self.translator = translator
        self.repo = drafts_repo(session, user.group_id, user.household_id)
        self.settings = get_kh_settings()

    def _source(
        self, url: str | None, text: str | None, images: list[UploadFile], media: UploadFile | None
    ) -> DraftSource:
        """The one source of a new draft; anything else is answered with 400 before something is stored. A
        recording is a text source: its transcript becomes the text."""
        given = [
            kind
            for kind, present in (
                (DraftSource.link, url),
                (DraftSource.text, text),
                (DraftSource.text, media),
                (DraftSource.image, images),
            )
            if present
        ]
        if media and not self.settings.whisper_url:
            raise bad_request("media_not_configured")
        if media and not (media.content_type or "").startswith(("audio/", "video/")):
            raise bad_request("not_audio_video")
        if url and is_video_link(url):  # never fetched (D5): text or photos that come along are the source
            given.remove(DraftSource.link)
            if not given:
                raise bad_request("video_link")
        if not given:
            raise bad_request("no_source")
        if len(given) > 1:
            raise bad_request("several_sources")
        if len(images) > self.settings.draft_max_images:
            raise bad_request("too_many_images")
        if text and len(text) > self.settings.draft_max_text:
            raise bad_request("text_too_long")
        return given[0]

    def create(
        self,
        url: str | None,
        text: str | None,
        images: list[UploadFile],
        media: UploadFile | None = None,
        caption: str | None = None,
    ) -> DraftOut:
        """Stores a new draft as working, with its originals or its recording; the route starts the recognition.
        CAPTION is the text that came with photos (a shared note): it is kept as the draft's text and read with them."""
        url, text = (url or "").strip() or None, (text or "").strip() or None
        source = self._source(url, text, images, media)
        if caption and len(caption) > self.settings.draft_max_text:
            raise bad_request("text_too_long")
        try:
            prepared = [prepare_original(upload.file.read(), self.settings.draft_max_image_mb) for upload in images]
        except ValueError as error:
            raise bad_request(str(error)) from error
        note = Path(media.filename or "").name[:MAX_NOTE] if media else None
        draft = self._insert(source, url, text or caption, note)
        if media:
            self._keep_recording(draft.id, media)
        return self._keep_originals(draft, prepared)

    def _insert(self, source: DraftSource, url: str | None, text: str | None, note: str | None) -> DraftOut:
        """The new working draft's row, without originals."""
        return self.repo.create(
            {
                "group_id": self.user.group_id,
                "household_id": self.user.household_id,
                "user_id": self.user.id,
                "status": DraftStatus.working,
                "source_type": source,
                "source_url": url,
                "source_url_normalized": normalize_url(url) if url else None,
                "source_text": text,
                "source_note": note,
            }
        )

    def _keep_originals(self, draft: DraftOut, prepared: list[Image.Image]) -> DraftOut:
        """Stores the prepared images with the draft; unwritable removes the draft again."""
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

    def create_from_file(self, filename: str, upload: UploadFile) -> FileImportOut:
        """New working drafts from an uploaded .txt, .md, .pdf or .zip file (D62, D84): each text one draft, each photo
        without a text of its own name one photo draft (a scanned PDF one draft of its images); a photo with a text's
        name is that draft's cover. The route starts the recognitions."""
        limit = self.settings.import_max_unzipped_mb * 1024 * 1024
        data = upload.file.read(limit + 1)
        if len(data) > limit:
            raise bad_request("file_too_large")
        try:
            content = read_file(filename, data, self.settings)
        except ValueError as error:
            raise bad_request(str(error)) from error
        created: list[DraftOut] = []
        for item in content.items:
            try:
                photos = [prepare_original(photo, self.settings.draft_max_image_mb) for photo in item.photos]
            except ValueError as error:
                content.skipped.append(SkippedFile(name=item.name, reason=str(error)))
                if item.text is None:
                    continue
                photos = []
            source = DraftSource.text if item.text else DraftSource.image
            draft = self._insert(source, None, item.text, Path(item.name).name[:MAX_NOTE])
            created.append(self._keep_originals(draft, photos))
        return FileImportOut(created=created, skipped=content.skipped)

    def create_shared(self, decision: ShareDecision, uploads: list[UploadFile]) -> FileImportOut:
        """New drafts from a share the way classify_share decided (D84); same checks as the other intakes. Photos
        beyond the draft limit are named as skipped."""
        match decision.kind:
            case ShareKind.photo:
                photos = [uploads[n] for n in decision.images]
                kept, extra = photos[: self.settings.draft_max_images], photos[self.settings.draft_max_images :]
                skipped = [SkippedFile(name=photo.filename or "", reason="too_many") for photo in extra]
                return FileImportOut(created=[self.create(None, None, kept, caption=decision.caption)], skipped=skipped)
            case ShareKind.pdf | ShareKind.file:
                return self.create_from_file(decision.value, uploads[decision.file])
            case ShareKind.link:
                return FileImportOut(created=[self.create(decision.value, None, [])], skipped=[])
            case ShareKind.text:
                return FileImportOut(created=[self.create(None, decision.value, [])], skipped=[])

    def _keep_recording(self, draft_id: UUID4, media: UploadFile) -> None:
        """Stores the recording with the draft; too big or unwritable removes the draft again."""
        try:
            store_media(draft_id, media.file, self.settings.draft_max_media_mb)
        except (ValueError, OSError) as error:
            remove_draft_dir(draft_id)
            self.repo.delete(draft_id)
            if isinstance(error, ValueError):
                raise bad_request(str(error)) from error
            raise

    def mark_stale(self) -> None:
        """Drafts that stayed working too long, e.g. after a restart mid-recognition, become failed. One that still
        has its recording may be waiting for Whisper, so it gets the longer RECORDING_STALE_AFTER."""
        now = get_utc_now()
        rows = self.session.execute(
            sa.select(KhDraft.id, KhDraft.update_at).where(
                KhDraft.group_id == self.user.group_id,
                KhDraft.household_id == self.user.household_id,
                KhDraft.status == DraftStatus.working,
                KhDraft.update_at < now - timedelta(minutes=self.settings.draft_stale_minutes),
            )
        ).all()
        stale = [
            draft_id
            for draft_id, changed in rows
            if not (media_path(draft_id).exists() and changed >= now - RECORDING_STALE_AFTER)
        ]
        if stale:
            self.session.execute(
                sa.update(KhDraft)
                .where(KhDraft.id.in_(stale), KhDraft.status == DraftStatus.working)
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
        """Sets a failed draft back to working; the route starts the recognition again. The switch is one
        conditional UPDATE, so of two retries at once exactly one wins and starts the recognition."""
        draft = self.get(draft_id)
        if draft.status != DraftStatus.failed:
            raise conflict("not_failed")
        claim = self.session.execute(
            sa.update(KhDraft)
            .where(KhDraft.id == draft_id, KhDraft.status == DraftStatus.failed)
            .values(status=DraftStatus.working, error=None, recipe=None, ai_model=None, warnings=[])
        )
        self.session.commit()
        if claim.rowcount == 0:  # type: ignore[attr-defined]
            raise conflict("not_failed")
        return self.get(draft_id)

    def _not_found(self) -> HTTPException:
        """404, as if the draft or origin did not exist."""
        return HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "not_found"})

    def _already_approved(self, draft: DraftOut) -> HTTPException:
        """409 that also says where the saved recipe is."""
        recipe = self._all_repos().recipes.get_one(draft.recipe_id, "id") if draft.recipe_id else None
        return conflict("already_approved", slug=recipe.slug if recipe else None)

    def edit(self, draft_id: UUID4, data: DraftEditIn, locale: str = DEFAULT_LOCALE) -> DraftOut:
        """Applies one edit from the review's preview to a ready draft's recipe and returns the draft."""
        draft = self.get(draft_id)
        if draft.status != DraftStatus.ready:
            raise conflict("not_ready")
        recipe = deepcopy(draft.recipe or {})
        if data.name is not None:
            edit_name(recipe, data.name)
        elif data.ingredient is not None:
            matcher = DataMatcher(self._household_repos())
            edit_ingredient(recipe, data.ingredient.index, data.ingredient.text, matcher, locale)
        elif data.step is not None:
            edit_step(recipe, data.step.index, data.step.text)
        # written only while the draft is still ready, so an edit racing an approval never lands in an approved draft
        written = self.session.execute(
            sa.update(KhDraft).where(KhDraft.id == draft_id, KhDraft.status == DraftStatus.ready).values(recipe=recipe)
        )
        self.session.commit()
        if written.rowcount == 0:  # type: ignore[attr-defined]
            raise conflict("not_ready")
        return self.get(draft_id)

    def reorder_originals(self, draft_id: UUID4, order: list[int]) -> DraftOut:
        """Puts a ready or failed draft's originals in the given order (current numbers from 1); the first becomes the
        cover and the first photo of a retry."""
        draft = self.get(draft_id)
        if draft.status not in (DraftStatus.ready, DraftStatus.failed):
            raise conflict("not_ready")
        if sorted(order) != list(range(1, len(draft.original_files) + 1)):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail={"code": "bad_order"})
        names = [draft.original_files[n - 1] for n in order]
        # written only while the draft is still open, so a racing approval or retry keeps its cover
        written = self.session.execute(
            sa.update(KhDraft)
            .where(KhDraft.id == draft_id, KhDraft.status.in_((DraftStatus.ready, DraftStatus.failed)))
            .values(original_files=names)
        )
        self.session.commit()
        if written.rowcount == 0:  # type: ignore[attr-defined]
            raise conflict("not_ready")
        return self.get(draft_id)

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

    def _save_recipe(self, draft: DraftOut, changes: dict[str, Any], linked: list[int] | None) -> RecipeOut:
        """Saves the recognized recipe with the review's changes the way Mealie's import does; a draft's
        first original (a photo draft's, or the photo that came with an imported text, D62) becomes the cover, like in
        Mealie's create_from_ai."""
        recipes = RecipeService(self._household_repos(), self.user, self.household, self.translator)
        recipe = recipes.create_one(RecipeDraft.model_validate({**(draft.recipe or {}), **changes}))
        try:
            save_amounts(self.session, draft.recipe or {}, recipe, linked)  # range ends, fixed lines, step links (D39)
            if draft.original_files:
                cover = original_path(draft.id, draft.original_files[0]).read_bytes()
                recipes.update_recipe_image(recipe.slug, cover, "webp")
        except Exception:
            # create_one has committed already; without this a retried approval would save the recipe twice
            self.session.rollback()
            recipes.delete_one(recipe.slug)
            raise
        return recipe

    def approve(self, draft_id: UUID4, data: ApproveIn) -> ApproveOut:
        """Saves a ready draft as a Mealie recipe; anyone in the household may. Servings and yield set in the
        review are saved with it. Possible duplicates that are new since the recognition stop it unless FORCE.
        The claim on the draft is one conditional UPDATE, so of two people approving at once exactly one wins."""
        draft = self.get(draft_id)
        if draft.status == DraftStatus.approved:
            raise self._already_approved(draft)
        if draft.status != DraftStatus.ready:
            raise conflict("not_ready")
        links = DraftAmounts.model_validate((draft.recipe or {}).get("khAmounts") or {}).step_amounts
        if any(not 0 <= index < len(links) for index in data.linked_steps or []):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail={"code": "linked_steps"})
        if not data.force and (new := self._new_duplicates(draft)):
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
            recipe = self._save_recipe(draft, data.recipe_changes(), data.linked_steps)
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
