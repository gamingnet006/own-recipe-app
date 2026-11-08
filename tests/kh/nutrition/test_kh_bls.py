"""KH: tests of the BLS table: reading the xlsx, the CSV rows, loading and the search (D44)."""

import io
import zipfile
from pathlib import Path

import pytest

from mealie.kh.nutrition import bls
from mealie.kh.nutrition.bls import BlsFood, load_bls, search_bls
from mealie.kh.nutrition.build_bls import SALT_PER_SODIUM, rows_from_xlsx, to_csv_rows

FIXTURE = Path(__file__).parent / "fixtures" / "bls.csv"

SHEET = (
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c>'
    '<c r="D1" t="s"><v>3</v></c></row>'
    '<row r="2"><c r="A2" t="s"><v>4</v></c><c r="B2" t="s"><v>5</v></c><c r="C2"><v>340</v></c>'
    '<c r="D2"><v>1.5</v></c></row>'
    '<row r="3"><c r="A3" t="s"><v>6</v></c><c r="B3" t="s"><v>7</v></c><c r="D3"><v>2</v></c></row>'
    "</sheetData></worksheet>"
)
STRINGS = ["BLS Code", "Lebensmittelbezeichnung", "ENERCC Energie [kcal/100g]", "Skipped", "X1", "Mehl", "X2", "Butter"]


def small_xlsx() -> bytes:
    """A tiny xlsx: shared strings, one empty cell (C3) and a column the caller does not keep (D)."""
    shared = "".join(f"<si><t>{s}</t></si>" for s in STRINGS)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as xlsx:
        xlsx.writestr(
            "xl/sharedStrings.xml",
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">{shared}</sst>',
        )
        xlsx.writestr("xl/worksheets/sheet1.xml", SHEET)
    return buffer.getvalue()


def test_rows_from_xlsx_reads_strings_numbers_and_empty_cells() -> None:
    rows = rows_from_xlsx(small_xlsx(), keep=lambda header: header != "Skipped")

    assert rows == [
        {"BLS Code": "X1", "Lebensmittelbezeichnung": "Mehl", "ENERCC Energie [kcal/100g]": "340"},
        {"BLS Code": "X2", "Lebensmittelbezeichnung": "Butter", "ENERCC Energie [kcal/100g]": ""},
    ]


def test_to_csv_rows_computes_salt_from_sodium() -> None:
    header = {
        "BLS Code": "X1",
        "Lebensmittelbezeichnung": "Mehl",
        "ENERCC Energie (Kilokalorien) [kcal/100g]": "340",
        "FAT Fett [g/100g]": "1.5",
        "NA Natrium [mg/100g]": "10",
    }
    food = to_csv_rows([header, {**header, "BLS Code": "X2", "NA Natrium [mg/100g]": ""}])

    assert food[0].code == "X1" and food[0].kcal == 340 and food[0].fat == 1.5
    assert food[0].salt == pytest.approx(10 * SALT_PER_SODIUM / 1000)
    assert food[0].protein is None  # no such column
    assert food[1].salt is None  # empty sodium


def test_load_bls_reads_empty_values_as_none() -> None:
    foods = load_bls(FIXTURE)

    assert foods["B100000"] == BlsFood("B100000", "Weizenmehl Type 405", 340, 1.0, 0.2, 70.0, 0.8, 10.0, 3.5, None)
    assert foods["B500000"].name == "Milch 3,5 % Fett"  # a comma inside quotes
    assert foods["C400000"].kcal is None
    assert load_bls(FIXTURE) is foods  # cached


def test_load_bls_default_path_is_the_shipped_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bls, "BLS_CSV", FIXTURE)

    assert "B100000" in load_bls()


def test_search_puts_names_starting_with_the_query_first_then_shorter_ones() -> None:
    foods = load_bls(FIXTURE)

    assert [f.name for f in search_bls("mehl", foods)] == ["Weizenmehl Type 405", "Roggenmehl Type 1150"]
    assert search_bls("kartoffel", foods)[0].name == "Kartoffel roh"
    assert [f.name for f in search_bls("TYPE 405", foods)] == ["Weizenmehl Type 405"]  # every word, any case


def test_search_finds_nothing_and_caps_at_the_limit() -> None:
    foods = load_bls(FIXTURE)

    assert search_bls("xyz", foods) == []
    assert search_bls("", foods) == []
    assert len(search_bls("e", foods, limit=3)) == 3


def test_search_prefix_beats_a_shorter_name_that_only_contains_the_word() -> None:
    foods = {
        "1": BlsFood("1", "Hefe", *[None] * 8),
        "2": BlsFood("2", "Mehl und Hefe", *[None] * 8),
        "3": BlsFood("3", "Hefe, frisch", *[None] * 8),
    }

    assert [f.code for f in search_bls("hefe", foods)] == ["1", "3", "2"]


def test_the_shipped_bls_csv_is_complete() -> None:
    foods = load_bls()

    assert len(foods) > 5000
    with_kcal = sum(1 for f in foods.values() if f.kcal is not None)
    assert with_kcal > 0.9 * len(foods)
