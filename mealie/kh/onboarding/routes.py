"""KH: /api/kh/onboarding (first sign-in, welcome and confirm-e-mail links) and /api/kh/admin/account-settings (D53)."""

from fastapi import APIRouter, Depends, Header, Request, Response
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.core.dependencies import get_auth_token
from mealie.db.db_setup import generate_session
from mealie.kh.accounts.sessions import new_session, session_payload
from mealie.kh.i18n.locale import installation_locale
from mealie.kh.onboarding import service
from mealie.kh.onboarding.schemas import (
    AccountSettingsIn,
    AccountSettingsOut,
    EmailIn,
    InstallationLocale,
    NewsSeenIn,
    OnboardingStatus,
    PasswordIn,
    TokenIn,
    TourIn,
    WelcomeIn,
    WelcomeInfo,
)
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter

router = UserAPIRouter(prefix="/onboarding")
public_router = APIRouter(prefix="/onboarding")  # the links in the mails are opened before anyone is signed in
admin_router = AdminAPIRouter(prefix="/admin/account-settings")
admin_tour_router = AdminAPIRouter(prefix="/admin/onboarding")


@controller(router)
class KhOnboardingController(BaseUserController):
    """What a signed-in person still has to do, and doing it."""

    @router.get("/me", response_model=OnboardingStatus)
    def get_status(self) -> OnboardingStatus:
        """Whether the person must choose a password or give an e-mail address."""
        return service.status_of(self.session, self.user)  # type: ignore[arg-type]

    @router.post("/password")
    def set_password(
        self, data: PasswordIn, request: Request, response: Response, token: str = Depends(get_auth_token)
    ):
        """Lets a new person choose their own password. That logs out every older session, also the ones opened with
        the admin's first password, so the answer is a fresh session token for this one."""
        session_payload(token)  # an API token is refused before the password changes
        service.set_own_password(self.session, self.user, data.password)  # type: ignore[arg-type]
        return new_session(request, response, token, self.user.id)

    @router.post("/tour-done")
    def tour_done(self) -> None:
        """The person finished or skipped the first-sign-in tour (D59)."""
        service.set_tour(self.session, self.user.id, False)

    @router.post("/news-seen")
    def news_seen(self, data: NewsSeenIn) -> None:
        """The person finished or skipped "Neu in Kochheft" up to this version (D69)."""
        service.set_news_seen(self.session, self.user.id, data.version)

    @router.post("/email")
    def request_email(self, data: EmailIn, accept_language: str | None = Header(None)) -> None:
        """Mails a confirm link to the address."""
        service.request_verification(self.session, self.user, data.email, accept_language)  # type: ignore[arg-type]


@public_router.post("/confirm-email")
def confirm_email(data: TokenIn, session: Session = Depends(generate_session)) -> None:
    """Confirms the address of a confirm link."""
    service.confirm_email(session, data.token)


@public_router.get("/locale", response_model=InstallationLocale)
def get_installation_locale(session: Session = Depends(generate_session)) -> InstallationLocale:
    """The installation's language (None until the first setup chose one), for the login page."""
    return InstallationLocale(locale=installation_locale(session))


@public_router.get("/welcome", response_model=WelcomeInfo)
def get_welcome(token: str, session: Session = Depends(generate_session)) -> WelcomeInfo:
    """Who a welcome link is for."""
    return service.welcome_info(session, token)


@public_router.post("/welcome")
def accept_welcome(data: WelcomeIn, session: Session = Depends(generate_session)) -> None:
    """Sets the password chosen on the welcome page."""
    service.accept_welcome(session, data.token, data.password)


@controller(admin_router)
class KhAccountSettingsController(BaseAdminController):
    """The admin's switch "e-mail required" and the installation's language."""

    def _current(self) -> AccountSettingsOut:
        return AccountSettingsOut(
            email_required=service.get_email_required(self.session), locale=installation_locale(self.session)
        )

    @admin_router.get("", response_model=AccountSettingsOut)
    def get_settings(self) -> AccountSettingsOut:
        return self._current()

    @admin_router.put("", response_model=AccountSettingsOut)
    def put_settings(self, data: AccountSettingsIn) -> AccountSettingsOut:
        """Saves the given parts; 400 when "e-mail required" is turned on without mail sending."""
        service.save_account_settings(self.session, data.email_required, data.locale)
        return self._current()


@controller(admin_tour_router)
class KhTourController(BaseAdminController):
    """The admin's choice of showing a new person the tour at the first sign-in (D59)."""

    @admin_tour_router.post("/{user_id}/tour")
    def put_tour(self, user_id: UUID4, data: TourIn) -> TourIn:
        """Sets or clears the tour of the user."""
        service.set_tour(self.session, user_id, data.tour)
        return data
