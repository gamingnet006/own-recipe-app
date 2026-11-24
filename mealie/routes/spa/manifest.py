import json
from urllib.parse import urlparse

from fastapi import Response

from mealie.core.config import get_app_settings
from mealie.db.db_setup import session_context  # KH: the installation language names the app
from mealie.kh.i18n.locale import installation_app_name  # KH: wave 2


def build_manifest() -> dict:  # KH: a function of its own, so the shopping page's manifest reuses it (D60)
    settings = get_app_settings()
    sub_path = urlparse(settings.BASE_URL).path or "/"
    with session_context() as session:  # KH: "Cookbook" for an English installation (wave 2)
        app_name = installation_app_name(session, settings.branding.name)

    manifest = {
        "name": app_name,  # KH: wave 2
        "short_name": app_name,
        "id": "/",
        "start_url": sub_path,
        "scope": sub_path,
        "display": "standalone",
        "background_color": "#1E1E1E",
        "theme_color": settings.theme.light_primary,
        "description": f"{app_name} is a recipe management and meal planning app",  # KH: app name (D49, wave 2)
        "lang": "en",
        "display_override": ["standalone", "minimal-ui", "browser", "window-controls-overlay"],
        "categories": ["food", "lifestyle"],
        "prefer_related_applications": False,
        "handle_links": "preferred",
        "launch_handler": {"client_mode": ["focus-existing", "auto"]},
        "edge_side_panel": {"preferred_width": 400},
        "share_target": {
            "action": "/r/create/url",
            "method": "GET",
            "enctype": "application/x-www-form-urlencoded",
            "params": {
                # 'url' is the field Chrome Android populates when sharing a page URL
                "url": "recipe_import_url",
                # 'text' is used by apps that share URLs as plain text; mapped to a
                # separate param so the page can fall back to it when 'url' is absent
                "text": "recipe_import_text",
            },
        },
        "icons": [
            {"src": "/icons/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icons/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {
                "src": "/icons/android-chrome-maskable-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable",
            },
            {
                "src": "/icons/android-chrome-maskable-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
        "screenshots": [
            {
                "src": "/screenshots/home-narrow.png",
                "sizes": "1600x2420",
                "form_factor": "narrow",
                "label": "Home Page",
            },
            {
                "src": "/screenshots/recipe-narrow.png",
                "sizes": "1600x2420",
                "form_factor": "narrow",
                "label": "Recipe Page",
            },
            {
                "src": "/screenshots/editor-narrow.png",
                "sizes": "1600x2420",
                "form_factor": "narrow",
                "label": "Editor Page",
            },
            {
                "src": "/screenshots/parser-narrow.png",
                "sizes": "1600x2420",
                "form_factor": "narrow",
                "label": "Parser Page",
            },
            {"src": "/screenshots/home-wide.png", "sizes": "2560x1460", "form_factor": "wide", "label": "Home Page"},
            {
                "src": "/screenshots/recipe-wide.png",
                "sizes": "2560x1460",
                "form_factor": "wide",
                "label": "Recipe Page",
            },
            {
                "src": "/screenshots/editor-wide.png",
                "sizes": "2560x1460",
                "form_factor": "wide",
                "label": "Editor Page",
            },
            {
                "src": "/screenshots/parser-wide.png",
                "sizes": "2560x1460",
                "form_factor": "wide",
                "label": "Parser Page",
            },
        ],
        "shortcuts": [
            {
                # KH: Kochheft's tile shopping page instead of Mealie's list overview (D60)
                "name": "Einkaufsliste",
                "short_name": "Einkauf",
                "description": "Open the shopping list",
                "url": "/einkauf",
                "icons": [
                    {"src": "/icons/mdiFormatListChecks-192x192.png", "sizes": "192x192"},
                    {"src": "/icons/mdiFormatListChecks-96x96.png", "sizes": "96x96"},
                ],
            },
            {
                "name": "Meal Planner",
                "short_name": "Meal Planner",
                "description": "Open the meal planner",
                "url": "/household/mealplan/planner/view",
                "icons": [
                    {"src": "/icons/mdiCalendarMultiselect-192x192.png", "sizes": "192x192"},
                    {"src": "/icons/mdiCalendarMultiselect-96x96.png", "sizes": "96x96"},
                ],
            },
        ],
    }
    return manifest


def manifest_response(manifest: dict) -> Response:  # KH: shared by both manifests (D60)
    return Response(
        content=json.dumps(manifest),
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


def serve_manifest():
    return manifest_response(build_manifest())  # KH: split up for D60
