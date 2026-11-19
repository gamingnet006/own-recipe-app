"""KH: the evening reminder's text (D75): which dishes are planned for tomorrow and what to prepare today.
Pure: takes plain data, so it is tested without a database."""

from dataclasses import dataclass, field

THAW_LABELS = {"fleisch", "fleischprodukte", "meeresfrüchte", "tiefkühlware"}
PREP_WORDS = ("über nacht", "am vortag", "einweichen", "marinieren")
SHORT_STEP = 60  # characters of a step shown in the hint


@dataclass
class PlannedRecipe:
    """What the reminder needs of one planned recipe: its name, its ingredients as (food, food label) and its steps."""

    name: str
    foods: list[tuple[str, str | None]] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)


def _short(step: str) -> str:
    """The step's first sentence, cut at a word when it is long."""
    text = " ".join(step.split())
    first = text.split(". ")[0].rstrip(".")
    if len(first) <= SHORT_STEP:
        return first
    return first[:SHORT_STEP].rsplit(" ", 1)[0] + " …"


def evening_message(recipes: list[PlannedRecipe]) -> tuple[str, str] | None:
    """(title, body) for tomorrow's recipes, or None when nothing is planned. The body holds the hints, one per line."""
    if not recipes:
        return None
    title = "Morgen: " + ", ".join(recipe.name for recipe in recipes)
    thaw = list(dict.fromkeys(food for r in recipes for food, label in r.foods if (label or "").lower() in THAW_LABELS))
    lines = [f"Denk ans Auftauen: {', '.join(thaw)}"] if thaw else []
    for recipe in recipes:
        for step in recipe.steps:
            if any(word in step.lower() for word in PREP_WORDS):
                lines.append(f"Am Vortag vorbereiten: {_short(step)}")
    return title, "\n".join(lines)
