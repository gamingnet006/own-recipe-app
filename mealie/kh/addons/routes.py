"""KH: the add-ons page's endpoints under /api/kh/addons (D46): everyone reads the household's switches, only admins
change them."""

from mealie.kh.addons.schemas import AddonFlags, AddonsOut
from mealie.kh.addons.service import load_addons, save_flags
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter

router = UserAPIRouter(prefix="/addons")
admin_router = AdminAPIRouter(prefix="/addons")


@controller(router)
class KhAddonsController(BaseUserController):
    """Reading the switches of the user's household."""

    @router.get("", response_model=AddonsOut)
    def get_addons(self) -> AddonsOut:
        """The switches as chosen and as in force, and which add-ons the host does not offer."""
        return load_addons(self.session, self.user.household_id)


@controller(admin_router)
class KhAddonsAdminController(BaseAdminController):
    """Changing the switches."""

    @admin_router.put("", response_model=AddonsOut)
    def put_addons(self, flags: AddonFlags) -> AddonsOut:
        """Stores all switches of the admin's household; data of switched-off add-ons stays untouched."""
        save_flags(self.session, self.user.household_id, flags)
        return load_addons(self.session, self.user.household_id)
