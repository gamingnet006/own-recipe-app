"""KH: reads Kochheft's own recipe text (D62) without AI. The format is written by recipeText() in
frontend/kh/app/lib/recipe-text.ts (D61); keep both in sync: the labels below are the ones that file writes, in
German and in English. The signature line says which language a text is in, so old German exports stay readable."""

import re
from dataclasses import dataclass

from mealie.schema.recipe.recipe import RecipeDraft
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_notes import RecipeNote
from mealie.schema.recipe.recipe_step import RecipeStep


@dataclass(frozen=True)
class Labels:
    """The words one language's export is written with."""

    signature: str
    servings: str
    ingredients: str
    steps: str
    notes: str
    source: str
    family_note: str  # the household's note (D82); read back as a Mealie note line
    times: dict[str, str]  # label to the draft field


GERMAN = Labels(
    "Exportiert aus Kochheft",
    "Portionen",
    "Zutaten:",
    "Zubereitung:",
    "Notizen:",
    "Quelle: ",
    "Unsere Notiz: ",
    {"Vorbereitung": "prep_time", "Zubereitung": "perform_time", "Gesamt": "total_time"},
)
ENGLISH = Labels(
    "Exported from Cookbook",
    "Servings",
    "Ingredients:",
    "Instructions:",
    "Notes:",
    "Source: ",
    "Our note: ",
    {"Prep time": "prep_time", "Cook time": "perform_time", "Total time": "total_time"},
)
BY_SIGNATURE = {labels.signature: labels for labels in (GERMAN, ENGLISH)}
SERVINGS = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(.*)$")
STEP_LINE = re.compile(r"^\d+\.\s+(\S.*)$")


def _info(lines: list[str], labels: Labels) -> dict[str, str | float]:
    """Servings and times of the line under the title ("Portionen: 4 · Gesamt: 1 Std."); unknown parts are ignored."""
    found: dict[str, str | float] = {}
    for part in " · ".join(lines).split(" · "):
        label, _, value = part.partition(":")
        label, value = label.strip(), value.strip()
        if label == labels.servings and (match := SERVINGS.match(value)):
            found["recipe_servings"] = float(match.group(1).replace(",", "."))
            if match.group(2):  # "12 Muffins": the yield as the recipe page shows it
                found["recipe_yield_quantity"] = found["recipe_servings"]
                found["recipe_yield"] = match.group(2)
        elif label in labels.times and value:
            found[labels.times[label]] = value
    return found


def _ingredients(lines: list[str]) -> list[RecipeIngredient]:
    """ "- " lines are ingredients (as text, the amount reading comes later); any other line is the title of the
    section that starts with the next ingredient."""
    result: list[RecipeIngredient] = []
    title: str | None = None
    for line in (raw.strip() for raw in lines):
        if not line:
            continue
        if line.startswith("- "):
            result.append(RecipeIngredient(note=line[2:].strip(), title=title))
            title = None
        else:
            title = line
    return result


def _steps(lines: list[str]) -> list[RecipeStep]:
    """ "1. " lines are steps; any other line is the title of the section that starts with the next step."""
    result: list[RecipeStep] = []
    title = ""
    for line in (raw.strip() for raw in lines):
        if not line:
            continue
        if match := STEP_LINE.match(line):
            result.append(RecipeStep(title=title, text=match.group(1)))
            title = ""
        else:
            title = line
    return result


def parse_kochheft_text(text: str) -> RecipeDraft | None:
    """The recipe in TEXT if it is Kochheft's own format, else None (the AI reads it then). The format is the
    title, an info line, "Zutaten:", "Zubereitung:", optional "Notizen:", "Unsere Notiz: " and "Quelle: ", and the
    signature line last (or the English labels, "Ingredients:" and so on, with "Exported from Cookbook")."""
    lines = text.strip().splitlines()
    labels = BY_SIGNATURE.get(lines[-1].strip()) if lines else None
    if labels is None:
        return None
    lines = [line.rstrip() for line in lines[:-1]]
    try:
        ingredients_at = lines.index(labels.ingredients)
        steps_at = lines.index(labels.steps, ingredients_at + 1)
    except ValueError:
        return None
    head = [line.strip() for line in lines[:ingredients_at] if line.strip()]
    if not head:
        return None

    tail = lines[steps_at + 1 :]
    source: str | None = None
    while tail and not tail[-1].strip():
        tail.pop()
    if tail and tail[-1].startswith(
        labels.source
    ):  # only the last line is the source; "Quelle: Oma" inside a note is a note
        source = tail.pop()[len(labels.source) :].strip() or None
    step_lines: list[str] = []
    note_lines: list[str] = []
    target = step_lines
    for line in tail:
        if line.startswith(labels.family_note):
            note_lines.append(line[len(labels.family_note) :].strip())
        elif line.strip() == labels.notes:
            target = note_lines
        else:
            target.append(line)
    notes = "\n".join(note_lines).strip()
    return RecipeDraft.model_validate(
        {
            "name": head[0],
            "orgURL": source,
            "recipe_ingredient": _ingredients(lines[ingredients_at + 1 : steps_at]),
            "recipe_instructions": _steps(step_lines),
            "notes": [RecipeNote(title="", text=notes)] if notes else [],
            **_info(head[1:], labels),
        }
    )
