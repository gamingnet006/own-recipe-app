"""KH: the nutrition tests' small BLS table and alias list, in place of the shipped files (D44)."""

from pathlib import Path

import pytest

from mealie.kh.nutrition import bls, mapping

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def small_bls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Points the app at the fixture's BLS table and alias list."""
    monkeypatch.setattr(bls, "BLS_CSV", FIXTURES / "bls.csv")
    monkeypatch.setattr(mapping, "ALIASES_JSON", FIXTURES / "aliases.json")
