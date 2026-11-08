"""KH: the BLS 4.0 table shipped with the app (D44): loading data/bls.csv once and searching it by name."""

import csv
import re
from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path

BLS_CSV = Path(__file__).parent / "data" / "bls.csv"
BLS_SEARCH_LIMIT = 20
SALT_PER_SODIUM = 2.5  # g salt per g sodium; the BLS table has sodium in mg


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


def compact(text: str) -> str:
    """TEXT lowercased without spaces and punctuation, so the BLS's "Weizen Mehl, Type 405" meets "weizenmehl"."""
    return re.sub(r"[\W_]+", "", text.lower())


def search_bls(query: str, foods: dict[str, BlsFood], limit: int = BLS_SEARCH_LIMIT) -> list[BlsFood]:
    """Foods whose name contains every word of QUERY (any case, spaces and punctuation of the name ignored, so
    "weizenmehl" finds "Weizen Mehl, Type 405"). Ranked: a name with a word equal to a query word, then a name
    starting with the query, then the rest; shorter names first within each. At most LIMIT."""
    words = query.lower().split()
    if not words:
        return []
    joined = "".join(compact(w) for w in words)

    def hit(food: BlsFood) -> bool:
        return all(w in food.name.lower() or compact(w) in compact(food.name) for w in words)

    def rank(food: BlsFood) -> tuple[bool, bool, int]:
        name_words = set(re.findall(r"\w+", food.name.lower()))
        return (not name_words & set(words), not compact(food.name).startswith(joined), len(food.name))

    return sorted(filter(hit, foods.values()), key=rank)[:limit]
