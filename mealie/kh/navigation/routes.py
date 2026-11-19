"""KH: the signed-in person's own side menu under /api/kh/navigation (D58)."""

from mealie.kh.navigation.schemas import NavigationSettings
from mealie.kh.navigation.service import load_hidden, save_hidden
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/navigation")


@controller(router)
class KhNavigationController(BaseUserController):
    """Reading and changing the own list; nobody reaches another person's."""

    @router.get("", response_model=NavigationSettings)
    def get_navigation(self) -> NavigationSettings:
        """The side-menu entries the user hid."""
        return NavigationSettings(hidden=load_hidden(self.session, self.user.id))

    @router.put("", response_model=NavigationSettings)
    def put_navigation(self, data: NavigationSettings) -> NavigationSettings:
        """Stores the list and returns it as stored (no duplicates, in the menu's order)."""
        save_hidden(self.session, self.user.id, data.hidden)
        return data
