"""KH: tests for the look "Salbei" (D38): Küchenhelfer's colors and name are the defaults, so every
installation shows them without any setting."""

from fastapi.testclient import TestClient

from tests.utils import api_routes


def test_the_look_is_sage(api_client: TestClient):
    theme = api_client.get(api_routes.app_about_theme).json()
    assert theme["lightPrimary"] == "#2F7A55"
    assert theme["darkPrimary"] == "#4FB07E"


def test_the_app_is_called_kuechenhelfer(api_client: TestClient):
    assert api_client.get(api_routes.app_about).json()["brandingName"] == "Küchenhelfer"
