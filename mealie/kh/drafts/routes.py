"""KH: the drafts API under /api/kh (phase 2): drafts under /drafts, a recipe's origin under /recipes.
Every route needs a logged-in user and sees only that user's household; recognition runs after the
response."""

from typing import Annotated

from fastapi import BackgroundTasks, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import UUID4

from mealie.kh.addons.service import ensure_addon
from mealie.kh.drafts.file_import import decode_text
from mealie.kh.drafts.recognize import recognize, recognize_all
from mealie.kh.drafts.schemas import ApproveIn, ApproveOut, DraftEditIn, DraftOut, FileImportOut, OriginOut, ShareOut
from mealie.kh.drafts.service import DraftService
from mealie.kh.drafts.share import SKIP_REASONS, SNIFF_BYTES, classify_share, share_confirmation
from mealie.kh.features.settings import get_kh_settings
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/drafts")
origin_router = UserAPIRouter(prefix="/recipes")


class _DraftsBase(BaseUserController):
    """The drafts service for this request's user and household."""

    @property
    def service(self) -> DraftService:
        """The drafts service for this request."""
        return DraftService(self.session, self.user, self.household, self.translator)


@controller(router)
class KhDraftsController(_DraftsBase):
    """Intake, list, review, retry, approval and discarding of the household's drafts."""

    def _recognize_later(self, tasks: BackgroundTasks, draft: DraftOut) -> None:
        """Queues the recognition to run once the response is sent."""
        tasks.add_task(recognize, draft.id, user=self.user, household=self.household, translator=self.translator)

    @router.post("", status_code=status.HTTP_201_CREATED, response_model=DraftOut)
    def create(
        self,
        tasks: BackgroundTasks,
        url: Annotated[str | None, Form()] = None,
        text: Annotated[str | None, Form()] = None,
        images: list[UploadFile] = File(default_factory=list),
        media: UploadFile | None = File(default=None),
        via: Annotated[str | None, Header(alias="X-KH-Via")] = None,
    ) -> DraftOut:
        """New draft from exactly one of a link, a text, up to KH_DRAFT_MAX_IMAGES images or, with a Whisper
        server, one audio or video recording."""
        # KH: add-ons (D46): the Telegram bot says it is the sender, recordings are the Whisper add-on
        if via == "telegram":
            ensure_addon(self.session, self.user.household_id, "telegram")
        if media and get_kh_settings().whisper_url:  # without a server the service answers "not configured"
            ensure_addon(self.session, self.user.household_id, "whisper")
        draft = self.service.create(url, text, images, media)
        self._recognize_later(tasks, draft)
        return draft

    @router.post("/file", status_code=status.HTTP_201_CREATED, response_model=FileImportOut)
    def create_from_file(self, tasks: BackgroundTasks, file: UploadFile = File(...)) -> FileImportOut:
        """New drafts from one uploaded .txt, .md or .zip file (D62); what made no draft is named in the answer."""
        result = self.service.create_from_file(file.filename or "", file)
        tasks.add_task(
            recognize_all,
            [draft.id for draft in result.created],
            user=self.user,
            household=self.household,
            translator=self.translator,
        )
        return result

    @staticmethod
    def _share_refused(code: str, message: str) -> HTTPException:
        """422 whose sentence is in the answer, because the shortcut shows it as it is; no page translates it."""
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail={"code": code, "message": message})

    @router.post("/share", status_code=status.HTTP_201_CREATED, response_model=ShareOut)
    def create_from_share(
        self,
        tasks: BackgroundTasks,
        file: UploadFile | None = File(default=None),
        text: Annotated[str | None, Form()] = None,
        url: Annotated[str | None, Form()] = None,
    ) -> ShareOut:
        """New draft(s) from whatever the iOS share shortcut sent (D84): a photo, PDF, text file or ZIP, a text or
        one or more links; Kochheft decides what it is (classify_share)."""
        head, file_text = b"", None
        if file:
            head = file.file.read(SNIFF_BYTES)
            file.file.seek(0)
            if text and file.filename and file.filename.lower().endswith((".txt", ".md")):
                # the text field is compared with the file's content (Shortcuts sends a text as both)
                file_text = decode_text(file.file.read(4 * get_kh_settings().draft_max_text))
                file.file.seek(0)
        decision = classify_share(file.filename or "" if file else None, head, text, url, file_text)
        if decision is None:
            raise self._share_refused("nothing_usable", "Damit kann Kochheft nichts anfangen.")
        result = self.service.create_shared(decision, file)
        if not result.created:  # all skipped: the shortcut must not say "in the inbox"
            reason = result.skipped[0].reason if result.skipped else ""
            raise self._share_refused(
                "nothing_created",
                f"Das hat nicht geklappt: {SKIP_REASONS.get(reason, 'Kochheft kann damit nichts anfangen')}.",
            )
        tasks.add_task(
            recognize_all,
            [draft.id for draft in result.created],
            user=self.user,
            household=self.household,
            translator=self.translator,
        )
        return ShareOut(created=result.created, skipped=result.skipped, message=share_confirmation(len(result.created)))

    @router.get("", response_model=list[DraftOut])
    def list_open(self) -> list[DraftOut]:
        """The household's drafts that are not approved yet, newest first."""
        return self.service.list_open()

    @router.get("/{draft_id}", response_model=DraftOut)
    def get_one(self, draft_id: UUID4) -> DraftOut:
        """One draft of the household."""
        return self.service.get(draft_id)

    @router.post("/{draft_id}/retry", response_model=DraftOut)
    def retry(self, draft_id: UUID4, tasks: BackgroundTasks) -> DraftOut:
        """Starts the recognition of a failed draft again."""
        draft = self.service.retry(draft_id)
        self._recognize_later(tasks, draft)
        return draft

    @router.patch("/{draft_id}/recipe", response_model=DraftOut)
    def edit_recipe(self, draft_id: UUID4, data: DraftEditIn) -> DraftOut:
        """Changes the name, one ingredient line or one step of a ready draft's recipe."""
        return self.service.edit(draft_id, data)

    @router.post("/{draft_id}/approve", response_model=ApproveOut)
    def approve(self, draft_id: UUID4, data: ApproveIn | None = None) -> ApproveOut:
        """Saves the draft as a recipe, with servings and yield from the review; {"force": true} also with
        possible duplicates that are new."""
        return self.service.approve(draft_id, data or ApproveIn())

    @router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
    def discard(self, draft_id: UUID4) -> None:
        """Deletes a ready or failed draft and its files."""
        self.service.discard(draft_id)

    @router.get("/{draft_id}/originals/{n}")
    def original(self, draft_id: UUID4, n: int) -> FileResponse:
        """The n-th original image (from 1) of a draft."""
        return FileResponse(self.service.original_file(draft_id, n), media_type="image/webp")


@controller(origin_router)
class KhOriginController(_DraftsBase):
    """Where an approved recipe came from, for the badge on the recipe page."""

    @origin_router.get("/{recipe_id}/origin", response_model=OriginOut)
    def origin(self, recipe_id: UUID4) -> OriginOut:
        """The origin of a recipe of the household; 404 for recipes without a draft."""
        return self.service.origin(recipe_id)
