"""KH: iOS Shortcuts read the answer of the two shortcut routes with "Wörterbuchwert für message" (D88), also on
errors. This handler adds a top-level German `message` next to the unchanged `detail` of every error there."""

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException

SPEAKABLE_PATHS = {"/api/kh/shopping/add", "/api/kh/drafts/share"}
CODE_SENTENCES = {  # codes of the drafts service that can end a share
    "video_link": "Videolinks lädt Kochheft nicht. Teile stattdessen den Text oder ein Foto.",
    "too_large": "Die Datei ist zu groß.",
    "file_too_large": "Die Datei ist zu groß.",
    "zip_too_large": "Die Datei ist zu groß.",
    "media_too_large": "Die Datei ist zu groß.",
    "text_too_long": "Der Text ist zu lang.",
    "not_an_image": "Das ist kein Foto.",
    "unreadable": "Die Datei lässt sich nicht lesen.",
    "empty": "Da ist nichts drin.",
    "unsupported": "Diesen Dateityp kann Kochheft nicht lesen.",
    "too_many_images": "Das sind zu viele Fotos.",
}
STATUS_SENTENCES = {
    401: "Du bist nicht angemeldet. Prüfe den API-Schlüssel im Kurzbefehl.",
    403: "Das ist nicht erlaubt.",
    404: "Das gibt es nicht.",
    413: "Die Datei ist zu groß.",
}


def speakable_message(status_code: int, detail: object) -> str:
    """The German sentence for an error: the detail's own message, else the sentence of its code, else one for the
    status."""
    if isinstance(detail, dict):
        if isinstance(detail.get("message"), str) and detail["message"]:
            return detail["message"]
        if detail.get("code") in CODE_SENTENCES:
            return CODE_SENTENCES[detail["code"]]
    return STATUS_SENTENCES.get(status_code, "Das hat nicht geklappt.")


async def kh_http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Mealie's default error answer, except on the shortcut routes, which also get a top-level `message`."""
    if request.url.path not in SPEAKABLE_PATHS:
        return await http_exception_handler(request, exc)
    return JSONResponse(
        {"detail": exc.detail, "message": speakable_message(exc.status_code, exc.detail)},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )
