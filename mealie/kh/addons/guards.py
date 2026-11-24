"""KH: route dependency that closes an add-on's endpoints while the household has it off (D46)."""

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from mealie.core.dependencies import get_current_user
from mealie.db.db_setup import generate_session
from mealie.kh.addons.service import addon_enabled, addon_refusal
from mealie.kh.i18n.messages import request_locale
from mealie.schema.user.user import PrivateUser


def require_addon(name: str) -> Callable[..., None]:
    """A dependency answering 403 for the logged-in user's household while the add-on NAME is off."""

    def check(
        request: Request,
        user: PrivateUser = Depends(get_current_user),
        session: Session = Depends(generate_session),
    ) -> None:
        if not addon_enabled(session, user.household_id, name):
            raise addon_refusal(name, request_locale(session, user.id, request))

    return check
