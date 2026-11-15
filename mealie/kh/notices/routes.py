"""KH: the bell's routes under /api/kh/notices (D39), for whoever manages the group's AI providers."""

from fastapi import status

from mealie.kh.notices.schemas import NoticeOut, NoticesOut
from mealie.kh.notices.service import mark_read, newest_notices, unread_count
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.permissions import Perm, require  # the route declares who may call it (Mealie 3.31)
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/notices")


@controller(router)
class KhNoticesController(BaseUserController):
    """The bell of the user's group."""

    @router.get("", response_model=NoticesOut, dependencies=[require(Perm.GROUP_MANAGE)])
    def notices(self) -> NoticesOut:
        """The group's 50 newest notices, newest first, and how many are unread."""
        items = [NoticeOut.model_validate(notice) for notice in newest_notices(self.session, self.group_id)]
        return NoticesOut(items=items, unread=unread_count(self.session, self.group_id, self.user.id))

    @router.post("/read", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require(Perm.GROUP_MANAGE)])
    def read(self) -> None:
        """Marks every notice so far as read, when the bell is opened."""
        mark_read(self.session, self.user.id)
