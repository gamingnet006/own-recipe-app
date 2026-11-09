"""KH: the profile (P7.4): leicht is the default, a value out of the four names stops the start."""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from mealie.kh.drafts.whisper import PROFILE_MODELS
from mealie.kh.features.settings import KhSettings


def test_the_profile_is_leicht_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("KH_PROFILE", raising=False)
    assert KhSettings().profile == "leicht"
    monkeypatch.setenv("KH_PROFILE", "")  # compose passes unset values as empty
    assert KhSettings().profile == "leicht"


@pytest.mark.parametrize("profile", ["leicht", "normal", "stark", "lokal"])
def test_the_four_profiles_are_read_from_the_environment(monkeypatch: pytest.MonkeyPatch, profile: str):
    monkeypatch.setenv("KH_PROFILE", profile)
    assert KhSettings().profile == profile


def test_an_unknown_profile_stops_the_start_naming_the_setting(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KH_PROFILE", "turbo")
    with pytest.raises(ValidationError, match="profile"):
        KhSettings()


def test_hardware_test_script_uses_the_same_whisper_models_as_the_backend():
    script = (Path(__file__).parents[3] / "kh" / "ops" / "hardware_test.sh").read_text()
    for profile, size in PROFILE_MODELS.items():
        assert re.search(rf"^\s*(?:\w+ \| )*{profile}(?: \| \w+)*\) echo {size} ;;", script, re.MULTILINE), profile
