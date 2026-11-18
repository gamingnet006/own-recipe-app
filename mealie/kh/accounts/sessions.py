"""KH: a fresh session token for a signed-in person, used by the household switch (D52) and after choosing the own
password (D53), which logs out every older session."""

import jwt
from fastapi import HTTPException, Request, Response, status
from pydantic import UUID4

from mealie.core import security
from mealie.core.config import get_app_settings
from mealie.routes.auth.auth import MealieAuthToken, set_session_cookie


def session_payload(current_token: str) -> dict:
    """The current token's claims; 400 for an API token, which must not turn into a session token. Called before any
    change a fresh session is meant to follow."""
    payload = jwt.decode(current_token, get_app_settings().SECRET, algorithms=[security.ALGORITHM])
    if payload.get("long_token"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "API tokens cannot be exchanged for a session token")
    return payload


def new_session(request: Request, response: Response, current_token: str, user_id: UUID4) -> dict:
    """Issues a session token for USER_ID the way /api/auth/refresh does: it keeps the remember-me choice of the
    current token and refuses API tokens, which must not turn into session tokens."""
    remember_me = bool(session_payload(current_token).get("rme", False))
    access_token, duration = security.create_access_token({"sub": str(user_id), "rme": remember_me})
    set_session_cookie(response, request, access_token, duration, remember_me)
    return MealieAuthToken.respond(access_token, duration)
