"""KH: the switch between a person's accounts under /api/kh/accounts, the admin's endpoints to give and take
away accounts (D52), and deleting the own account (D78)."""

from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import UUID4

from mealie.core.dependencies import get_auth_token
from mealie.db.models.users.users import User
from mealie.kh.accounts import removal, service
from mealie.kh.accounts.schemas import AccountOut, DeleteIn, DeletePreviewOut, HeirOut, LinkIn, PersonOut, SwitchIn
from mealie.kh.accounts.sessions import new_session, session_payload
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter
from mealie.routes.auth.auth import SESSION_COOKIE_NAME, session_cookie_attrs

router = UserAPIRouter(prefix="/accounts")
own_router = UserAPIRouter(prefix="/account")
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

    @admin_router.get("/{user_id}/heir", response_model=HeirOut | None)
    def heir(self, user_id: UUID4) -> HeirOut | None:
        """Who would take over this user's recipes when an admin deletes them; None when nobody else lives there."""
        user = self.session.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return removal.as_heir(removal.default_heir(self.session, user))

    @admin_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    def unlink(self, user_id: UUID4) -> None:
        """Dissolves the link; the account stays and can be deleted under Admin > Users."""
        service.unlink_account(self.session, user_id)


@controller(own_router)
class KhOwnAccountController(BaseUserController):
    """A person deleting their own account; their recipes and lists stay with the household."""

    def _orm_user(self) -> User:
        return self.session.get(User, self.user.id)

    @own_router.get("/delete-preview", response_model=DeletePreviewOut)
    def delete_preview(self) -> DeletePreviewOut:
        """Who would inherit, how many recipes and lists that is, and why deleting is not possible (or None)."""
        user = self._orm_user()
        plan = removal.plan_own_deletion(self.session, user)
        heir_id = plan.heirs[user.id]
        return DeletePreviewOut(
            heir=removal.as_heir(self.session.get(User, heir_id) if heir_id else None),
            recipes=plan.owned.recipes,
            lists=plan.owned.lists,
            blocked=plan.blocked,
        )

    @own_router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
    def delete(
        self, data: DeleteIn, request: Request, response: Response, token: str = Depends(get_auth_token)
    ) -> None:
        """Deletes the signed-in person's accounts when CONFIRM is the username; signs the browser out. Not for API
        tokens (400), and 409 with the reason when the person is the last admin or the last one in a household."""
        session_payload(token)
        user = self._orm_user()
        if data.confirm.strip().lower() != (user.username or "").lower():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Der Benutzername stimmt nicht.")
        try:
            removal.delete_own_accounts(self.session, user)
        except ValueError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
        # same attributes as /api/auth/logout, or the browser keeps the cookie
        response.set_cookie(SESSION_COOKIE_NAME, "", max_age=0, expires=0, **session_cookie_attrs(request))
