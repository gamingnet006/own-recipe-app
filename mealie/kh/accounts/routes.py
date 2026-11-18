"""KH: the switch between a person's accounts under /api/kh/accounts, and the admin's endpoints to give and take
away accounts (D52)."""

from fastapi import Depends, Request, Response, status
from pydantic import UUID4

from mealie.core.dependencies import get_auth_token
from mealie.kh.accounts import service
from mealie.kh.accounts.schemas import AccountOut, LinkIn, PersonOut, SwitchIn
from mealie.kh.accounts.sessions import new_session
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter

router = UserAPIRouter(prefix="/accounts")
admin_router = AdminAPIRouter(prefix="/admin/accounts")


@controller(router)
class KhAccountsController(BaseUserController):
    """Listing the person's accounts and switching to one."""

    @router.get("", response_model=list[AccountOut])
    def get_accounts(self) -> list[AccountOut]:
        """The person's accounts with the current one marked; empty when there is nothing to switch to."""
        return service.accounts_of(self.session, self.user.id)

    @router.post("/switch")
    def switch(self, data: SwitchIn, request: Request, response: Response, token: str = Depends(get_auth_token)):
        """Signs the person in to another of their accounts, without a password. Like /api/auth/refresh the new
        token keeps the remember-me choice, and API tokens are refused."""
        service.prepare_switch(self.session, self.user.id, data.user_id)
        return new_session(request, response, token, data.user_id)


@controller(admin_router)
class KhAccountsAdminController(BaseAdminController):
    """Giving a person an account in another household, and taking it away."""

    @admin_router.get("", response_model=list[PersonOut])
    def get_people(self) -> list[PersonOut]:
        """All persons with their accounts."""
        return service.all_people(self.session)

    @admin_router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
    def link(self, data: LinkIn) -> AccountOut:
        """Creates the person's account in the household."""
        return service.link_account(self.repos, data.user_id, data.household_id)

    @admin_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    def unlink(self, user_id: UUID4) -> None:
        """Dissolves the link; the account stays and can be deleted under Admin > Users."""
        service.unlink_account(self.session, user_id)
