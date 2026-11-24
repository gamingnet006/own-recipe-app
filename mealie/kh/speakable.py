"""KH: iOS Shortcuts read the answer of the two shortcut routes with "Wörterbuchwert für message" (D88), also on
errors. This handler adds a top-level `message` in the person's language next to the unchanged `detail` of every
error there."""

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException

from mealie.db.db_setup import session_context
from mealie.kh.i18n.locale import DEFAULT_LOCALE, Locale, person_locale
from mealie.kh.i18n.messages import say

SPEAKABLE_PATHS = {"/api/kh/shopping/add", "/api/kh/drafts/share"}
CODE_KEYS = {  # codes of the drafts service that can end a share, and the sentence (in messages.py) each one gets
    "video_link": "code_video_link",
    "too_large": "code_too_large",
    "file_too_large": "code_too_large",
    "zip_too_large": "code_too_large",
    "media_too_large": "code_too_large",
    "text_too_long": "code_text_too_long",
    "not_an_image": "code_not_an_image",
    "unreadable": "code_unreadable",
    "empty": "code_empty",
    "unsupported": "code_unsupported",
    "too_many_images": "code_too_many_images",
}
STATUS_KEYS = {401: "status_401", 403: "status_403", 404: "status_404", 413: "code_too_large"}


def speakable_message(status_code: int, detail: object, locale: Locale = DEFAULT_LOCALE) -> str:
    """The sentence for an error in LOCALE: the detail's own message, else the sentence of its code, else one for the
    status."""
    if isinstance(detail, dict):
        if isinstance(detail.get("message"), str) and detail["message"]:
            return detail["message"]
        if detail.get("code") in CODE_KEYS:
            return say(CODE_KEYS[detail["code"]], locale)
    return say(STATUS_KEYS.get(status_code, "status_other"), locale)


def _error_locale(request: Request) -> Locale:
    """The language the route settled on; an error before that (no valid key) falls back to Accept-Language, then the
    installation's language."""
    if locale := getattr(request.state, "kh_locale", None):
        return locale
    with session_context() as session:
        return person_locale(session, None, request.headers.get("accept-language"))


async def kh_http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Mealie's default error answer, except on the shortcut routes, which also get a top-level `message`."""
    if request.url.path not in SPEAKABLE_PATHS:
        return await http_exception_handler(request, exc)
    return JSONResponse(
        {"detail": exc.detail, "message": speakable_message(exc.status_code, exc.detail, _error_locale(request))},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )
