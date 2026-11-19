"""KH: the manifest of the shopping page (D60): Mealie's own with another name and start page, so "Add to Home
Screen" on /einkauf makes an app of its own that opens the shopping list."""

from fastapi import Response

from mealie.routes.spa.manifest import build_manifest, manifest_response

SHOPPING_PATH = "/einkauf"


def serve_shopping_manifest() -> Response:
    """The main manifest with the id, names and start page of the shopping list; the scope stays, so links work."""
    return manifest_response(
        {
            **build_manifest(),
            "id": SHOPPING_PATH,
            "name": "Einkauf",
            "short_name": "Einkauf",
            "start_url": SHOPPING_PATH,
        }
    )
