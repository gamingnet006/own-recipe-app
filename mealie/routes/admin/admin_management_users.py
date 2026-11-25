from functools import cached_property

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import UUID4

from mealie.core import security
from mealie.kh.accounts.removal import admin_heir, transfer_and_delete  # KH: recipes stay when a user goes (D78)
from mealie.kh.accounts.service import sync_linked_rights  # KH: a user's account links (D52)
from mealie.kh.i18n.locale import person_locale  # KH: the refusals are in the admin's language
from mealie.kh.onboarding.service import (  # KH: accounts without e-mail (D53)
    after_admin_create,
    email_or_stored,
    placeholder_email,
)
from mealie.routes._base import BaseAdminController, controller
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.permissions import forbidden
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import ErrorResponse
from mealie.schema.user.auth import UnlockResults
from mealie.schema.user.user import UserIn, UserOut, UserPagination
from mealie.schema.user.user_passwords import ForgotPassword, PasswordResetToken
from mealie.services.user_services.password_reset_service import PasswordResetService
from mealie.services.user_services.user_service import UserService

router = APIRouter(prefix="/users")


@controller(router)
class AdminUserManagementRoutes(BaseAdminController):
    @cached_property
    def repo(self):
        return self.repos.users

    # =======================================================================
    # CRUD Operations

    @property
    def mixins(self):
        return HttpRepo[UserIn, UserOut, UserOut](self.repo, self.logger, self.registered_exceptions)

    @router.get("", response_model=UserPagination)
    def get_all(self, q: PaginationQuery = Depends(PaginationQuery)):
        response = self.repo.page_all(
            pagination=q,
            override=UserOut,
        )

        response.set_pagination_guides(router.url_path_for("get_all"), q.model_dump())
        return response

    @router.post("", response_model=UserOut, status_code=201)
    def create_one(self, data: UserIn, accept_language: str | None = Header(None)):
        data.email = data.email.strip() or placeholder_email()  # KH: blank e-mail becomes a placeholder (D53)
        if self.repos.users.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, {"message": self.t("exceptions.username-conflict-error")})
        elif self.repos.users.get_one(data.email, "email"):
            raise HTTPException(status.HTTP_409_CONFLICT, {"message": self.t("exceptions.email-conflict-error")})

        data.password = security.hash_password(data.password)
        created = self.mixins.create_one(data)
        # KH: first-sign-in flag and welcome mail (D53)
        after_admin_create(self.session, created.id, created.email, created.username, accept_language)
        return created

    @router.post("/unlock", response_model=UnlockResults)
    def unlock_users(self, force: bool = False) -> UnlockResults:
        user_service = UserService(self.repos)
        unlocked = user_service.reset_locked_users(force=force)

        return UnlockResults(unlocked=unlocked)

    @router.get("/{item_id}", response_model=UserOut)
    def get_one(self, item_id: UUID4):
        return self.mixins.get_one(item_id)

    @router.put("/{item_id}", response_model=UserOut)
    def update_one(self, item_id: UUID4, data: UserOut):
        # Prevent self demotion
        if self.user.id == item_id and self.user.admin != data.admin:
            raise forbidden("you cannot demote yourself")

        data.email = email_or_stored(self.session, item_id, data.email)  # KH: blank keeps the stored e-mail (D53)
        updated = self.mixins.update_one(data, item_id)
        sync_linked_rights(self.session, item_id)  # KH: linked accounts get the same rights at once (D52)
        return updated

    @router.delete("/{item_id}", response_model=UserOut)
    def delete_one(self, item_id: UUID4, transfer_to: UUID4 | None = Query(None, alias="transferTo")):
        deleted = self.mixins.get_one(item_id)
        # KH: the recipes, lists and plans go to a person of the household and the person's own rows are cleaned up
        # (D78, which holds the former D44/D52/D53/D58/D75 clean-up); SQLite in Mealie skips cascades
        transfer_and_delete(
            self.session,
            item_id,
            admin_heir(self.session, item_id, transfer_to, person_locale(self.session, self.user.id, None)),
        )  # KH: the admin's language
        return deleted

    @router.post("/password-reset-token", response_model=PasswordResetToken, status_code=201)
    def generate_token(self, email: ForgotPassword):
        """Generates a reset token and returns it. This is an authenticated endpoint"""
        f_service = PasswordResetService(self.session)
        token_entry = f_service.generate_reset_token(email.email)
        if not token_entry:
            raise HTTPException(status_code=500, detail=ErrorResponse.respond("error while generating reset token"))
        return PasswordResetToken(token=token_entry.token)
