"""KH: the signed-in person's own side menu under /api/kh/navigation (D58), and the admin's simple view switch for
another person (D79)."""

from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.db.models.users.users import User
from mealie.kh.navigation.schemas import NavigationSettings, SimpleView
from mealie.kh.navigation.service import load_navigation, save_navigation
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter

router = UserAPIRouter(prefix="/navigation")
admin_router = AdminAPIRouter(prefix="/admin/navigation")


@controller(router)
class KhNavigationController(BaseUserController):
    """Reading and changing the own list; nobody reaches another person's."""

    @router.get("", response_model=NavigationSettings)
    def get_navigation(self) -> NavigationSettings:
        """The side-menu entries the user hid and whether the simple view is on."""
        return load_navigation(self.session, self.user.id)

    @router.put("", response_model=NavigationSettings)
    def put_navigation(self, data: NavigationSettings) -> NavigationSettings:
        """Stores the given parts and returns the result (no duplicates, in the menu's order)."""
        save_navigation(self.session, self.user.id, data.hidden, data.simple, data.locale, data.accent)
        return load_navigation(self.session, self.user.id)


@controller(admin_router)
class KhNavigationAdminController(BaseAdminController):
    """The admin switches the simple view for someone else, e.g. a family member new to apps."""

    def _person(self, user_id: UUID4) -> UUID4:
        # the admin may switch anyone; an unknown id is the only 404
        if self.session.get(User, user_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return user_id

    @admin_router.get("/{user_id}", response_model=SimpleView)
    def get_simple(self, user_id: UUID4) -> SimpleView:
        """Whether the person's simple view is on."""
        return SimpleView(simple=bool(load_navigation(self.session, self._person(user_id)).simple))

    @admin_router.put("/{user_id}", response_model=SimpleView)
    def put_simple(self, user_id: UUID4, data: SimpleView) -> SimpleView:
        """Switches the person's simple view on or off."""
        save_navigation(self.session, self._person(user_id), simple=data.simple)
        return data
