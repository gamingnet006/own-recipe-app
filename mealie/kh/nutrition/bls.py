"""KH: the BLS 4.0 table shipped with the app (D44): loading data/bls.csv once and searching it by name."""

import csv
from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path

BLS_CSV = Path(__file__).parent / "data" / "bls.csv"
BLS_SEARCH_LIMIT = 20


@dataclass(frozen=True)
class BlsFood:
    """One BLS food with its values per 100 g edible part; a value the BLS does not have is None."""

    code: str
    name: str
    kcal: float | None
    fat: float | None
    saturated: float | None
    carbs: float | None
    sugar: float | None
    protein: float | None
    fiber: float | None
    salt: float | None


FIELDS = [f.name for f in fields(BlsFood)]  # the CSV's columns, in order


@lru_cache
def _load(path: Path) -> dict[str, BlsFood]:
    """Reads the CSV at PATH; an empty value becomes None. Cached per path."""
    with path.open(newline="", encoding="utf-8") as file:
        return {
            row["code"]: BlsFood(
                row["code"],
                row["name"],
                *[float(row[f]) if row[f] != "" else None for f in FIELDS[2:]],
            )
            for row in csv.DictReader(file)
        }


def load_bls(path: Path | None = None) -> dict[str, BlsFood]:
    """The BLS foods by code, from PATH or the shipped file; read once, then cached."""
    return _load(path or BLS_CSV)


def search_bls(query: str, foods: dict[str, BlsFood], limit: int = BLS_SEARCH_LIMIT) -> list[BlsFood]:
    """Foods whose name contains every word of QUERY (any case); names starting with the first word come first,
    then shorter names. At most LIMIT."""
    words = query.lower().split()
    if not words:
        return []
    hits = [f for f in foods.values() if all(w in f.name.lower() for w in words)]
    hits.sort(key=lambda f: (not f.name.lower().startswith(words[0]), len(f.name)))
    return hits[:limit]
