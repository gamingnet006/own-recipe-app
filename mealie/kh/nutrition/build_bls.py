"""KH: builds data/bls.csv from the official BLS 4.0 ZIP (D44). Run once by a developer, never at runtime:
`uv run python -m mealie.kh.nutrition.build_bls`. Standard library only; the xlsx is read as data, nothing in it runs.

BLS 4.0 (Max Rubner-Institut, 2025, CC BY 4.0), values per 100 g edible part. See docs/kh/THIRD_PARTY_NOTICES.md."""

import csv
import hashlib
import io
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable
from pathlib import Path

from mealie.kh.nutrition.bls import BLS_CSV, FIELDS, SALT_PER_SODIUM, BlsFood

BLS_ZIP_URL = "https://www.blsdb.de/assets/uploads/BLS_4_0_2025_DE.zip"
BLS_ZIP_SHA256 = "12b7a6ba62807ec9b301eb276f897dc85f99b2292311618dec3749a12d984c91"
DOWNLOAD_TIMEOUT_SECONDS = 120
XLSX_IN_ZIP = "BLS_4_0_2025_DE/BLS_4_0_Daten_2025_DE.xlsx"

CODE_HEADER = "BLS Code"
NAME_HEADER = "Lebensmittelbezeichnung"  # the German name; "Food name" is the English one
# BLS nutrient codes (the first word of a value column's header, e.g. "ENERCC Energie (Kilokalorien) [kcal/100g]")
NUTRIENT_CODES = {
    "kcal": "ENERCC",  # energy in kcal (ENERCJ is kJ)
    "fat": "FAT",
    "saturated": "FASAT",  # fatty acids, saturated, total
    "carbs": "CHO",  # carbohydrates, available
    "sugar": "SUGAR",  # mono- and disaccharides, total
    "protein": "PROT625",  # protein, N x 6.25
    "fiber": "FIBT",  # dietary fibre, total
    "sodium": "NA",  # mg; salt is computed from it
}
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def is_wanted_header(header: str) -> bool:
    """Whether the column is the code, the German name or one of the nutrient value columns we read."""
    if header in (CODE_HEADER, NAME_HEADER):
        return True
    return "[" in header and header.split(" ", 1)[0] in NUTRIENT_CODES.values()


def _column_letters(ref: str) -> str:
    """The column part of a cell reference: "AB12" gives "AB"."""
    return "".join(ch for ch in ref if ch.isalpha())


def rows_from_xlsx(data: bytes, keep: Callable[[str], bool] = lambda header: True) -> list[dict[str, str]]:
    """The first sheet of the xlsx DATA as one dict per row below the header row, keyed by header text. Only columns
    whose header KEEP accepts are read (the file has 400+ columns); an empty cell is ''."""
    with zipfile.ZipFile(io.BytesIO(data)) as xlsx:
        strings = [
            "".join(t.text or "" for t in si.iter(f"{{{MAIN}}}t"))
            for si in ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
        ]
        headers: dict[str, str] = {}  # column letters -> kept header
        rows: list[dict[str, str]] = []
        for _, element in ET.iterparse(xlsx.open("xl/worksheets/sheet1.xml")):
            if element.tag != f"{{{MAIN}}}row":
                continue
            cells = {}
            for cell in element:
                value = cell.find(f"{{{MAIN}}}v")
                if value is not None and value.text is not None:
                    cells[_column_letters(cell.get("r", ""))] = (
                        strings[int(value.text)] if cell.get("t") == "s" else value.text
                    )
            if not headers:
                headers = {col: text for col, text in cells.items() if keep(text)}
            else:
                rows.append({header: cells.get(col, "") for col, header in headers.items()})
            element.clear()
    return rows


def _number(text: str) -> float | None:
    """TEXT as a number, or None if it is empty or not a number."""
    try:
        return float(text)
    except ValueError:
        return None


def to_csv_rows(rows: list[dict[str, str]]) -> list[BlsFood]:
    """One BlsFood per row, from the nutrient columns named in NUTRIENT_CODES; salt is sodium (mg) times
    SALT_PER_SODIUM per 1000, g per 100 g. A missing column or value gives None."""
    by_code: dict[str, str] = {}
    if rows:
        by_code = {h.split(" ", 1)[0]: h for h in rows[0] if "[" in h}
    foods = []
    for row in rows:
        values = {name: _number(row.get(by_code.get(code, ""), "")) for name, code in NUTRIENT_CODES.items()}
        sodium = values.pop("sodium")
        salt = None if sodium is None else round(sodium * SALT_PER_SODIUM / 1000, 3)
        foods.append(BlsFood(row[CODE_HEADER], row[NAME_HEADER], **values, salt=salt))
    return foods


def write_csv(foods: list[BlsFood], path: Path) -> None:
    """Writes FOODS to PATH with the columns of BlsFood; None becomes an empty value."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for food in foods:
            writer.writerow(["" if (v := getattr(food, f)) is None else v for f in FIELDS])


def main() -> None:
    """Downloads the BLS ZIP, checks its SHA-256, and writes the CSV next to bls.py."""
    with urllib.request.urlopen(BLS_ZIP_URL, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310 (fixed https URL)
        archive = response.read()
    digest = hashlib.sha256(archive).hexdigest()
    if digest != BLS_ZIP_SHA256:
        raise SystemExit(f"BLS ZIP has SHA-256 {digest}, expected {BLS_ZIP_SHA256}; not writing anything")
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        xlsx = zipped.read(XLSX_IN_ZIP)
    foods = to_csv_rows(rows_from_xlsx(xlsx, keep=is_wanted_header))
    write_csv(foods, BLS_CSV)
    print(f"Wrote {len(foods)} foods to {BLS_CSV}")  # noqa: T201 (a developer script)


if __name__ == "__main__":
    main()
