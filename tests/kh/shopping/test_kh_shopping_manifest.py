"""KH: tests for the two web manifests (D60): the main one gets the shopping shortcut, the shopping page's one starts
at /einkauf, and both are served without signing in."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mealie.kh.shopping.manifest import serve_shopping_manifest
from mealie.routes.spa.manifest import serve_manifest


def client() -> TestClient:
    app = FastAPI()
    app.get("/manifest.webmanifest")(serve_manifest)
    app.get("/einkauf.webmanifest")(serve_shopping_manifest)
    return TestClient(app)


def test_main_manifest_has_the_shopping_shortcut():
    manifest = client().get("/manifest.webmanifest").json()
    shortcut = next(item for item in manifest["shortcuts"] if item["url"] == "/einkauf")
    assert shortcut["name"] == "Einkaufsliste"
    assert any(icon["sizes"] == "192x192" for icon in shortcut["icons"])
    assert manifest["id"] == "/"
    assert manifest["start_url"] == "/"


def test_shopping_manifest_starts_at_the_shopping_page():
    response = client().get("/einkauf.webmanifest")
    assert response.headers["content-type"] == "application/manifest+json"
    manifest = response.json()
    assert (manifest["id"], manifest["start_url"]) == ("/einkauf", "/einkauf")
    assert (manifest["name"], manifest["short_name"]) == ("Einkauf", "Einkauf")
    assert manifest["scope"] == "/"
    assert manifest["icons"] == client().get("/manifest.webmanifest").json()["icons"]
