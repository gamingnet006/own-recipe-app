"""KH: route dependency that closes an add-on's endpoints while the household has it off (D46)."""

from collections.abc import Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from mealie.core.dependencies import get_current_user
from mealie.db.db_setup import generate_session
from mealie.kh.addons.service import ensure_addon
from mealie.schema.user.user import PrivateUser


def require_addon(name: str) -> Callable[..., None]:
    """A dependency answering 403 for the logged-in user's household while the add-on NAME is off."""

    def check(user: PrivateUser = Depends(get_current_user), session: Session = Depends(generate_session)) -> None:
        ensure_addon(session, user.household_id, name)

    return check
