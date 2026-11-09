"""KH: the drafts API under /api/kh (phase 2): drafts under /drafts, a recipe's origin under /recipes.
Every route needs a logged-in user and sees only that user's household; recognition runs after the
response."""

from typing import Annotated

from fastapi import BackgroundTasks, File, Form, Header, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import UUID4

from mealie.kh.addons.service import ensure_addon
from mealie.kh.drafts.recognize import recognize
from mealie.kh.drafts.schemas import ApproveIn, ApproveOut, DraftOut, OriginOut
from mealie.kh.drafts.service import DraftService
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
        if media:
            ensure_addon(self.session, self.user.household_id, "whisper")
        draft = self.service.create(url, text, images, media)
        self._recognize_later(tasks, draft)
        return draft

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
