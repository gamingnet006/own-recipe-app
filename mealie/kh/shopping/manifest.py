"""KH: the manifest of the shopping page (D60): Mealie's own with another name and start page, so "Add to Home
Screen" on /einkauf makes an app of its own that opens the shopping list."""

from fastapi import Response

from mealie.db.db_setup import session_context
from mealie.kh.i18n.locale import DEFAULT_LOCALE, installation_locale
from mealie.kh.i18n.messages import say
from mealie.routes.spa.manifest import build_manifest, manifest_response

SHOPPING_PATH = "/einkauf"


def serve_shopping_manifest() -> Response:
    """The main manifest with the id, names and start page of the shopping list; the scope stays, so links work."""
    with session_context() as session:
        locale = installation_locale(session) or DEFAULT_LOCALE
    return manifest_response(
        {
            **build_manifest(),
            "id": SHOPPING_PATH,
            "name": say("manifest_shopping_short", locale),
            "short_name": say("manifest_shopping_short", locale),
            "start_url": SHOPPING_PATH,
        }
    )
