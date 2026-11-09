"""KH: tests for the look "Salbei" (D38): Kochheft's colors and name are the defaults, so every
installation shows them without any setting."""

from fastapi.testclient import TestClient

from tests.utils import api_routes


def test_the_look_is_sage(api_client: TestClient):
    theme = api_client.get(api_routes.app_about_theme).json()
    assert theme["lightPrimary"] == "#2F7A55"
    assert theme["darkPrimary"] == "#4FB07E"


def test_warnings_and_errors_are_readable_on_light_ground(api_client: TestClient):
    theme = api_client.get(api_routes.app_about_theme).json()
    assert theme["lightWarning"] == "#8F4512"
    assert theme["lightError"] == "#B42318"


def test_the_app_is_called_kuechenhelfer(api_client: TestClient):
    assert api_client.get(api_routes.app_about).json()["brandingName"] == "Kochheft"
