"""KH: possible duplicates of a draft (phase 2): the same link after cleaning, a similar title, or many of
the same ingredients under a halfway similar title. Only hints for the review; nothing is ever deleted."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import UUID4

from mealie.kh.drafts.repository import drafts_repo
from mealie.kh.drafts.schemas import DraftStatus, DraftWarning
from mealie.kh.features.settings import KhSettings
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import Recipe

# Query parameters that only track where a link was shared, never which page it is
TRACKING = re.compile(r"^(utm_.*|fbclid|gclid|igshid|igsh|si|ref)$")
# Words that do not tell recipes apart: "Omas Apfelkuchen" and "Apfelkuchen nach Oma" are one dish
FILLER_WORDS = {"nach", "von", "vom", "mit", "und", "a", "la", "der", "die", "das", "ein", "eine", "mein", "meine"}
UNITS = {"g", "kg", "mg", "ml", "l", "el", "tl", "prise", "stück", "packung", "becher", "tasse", "cup", "tbsp", "tsp"}


@dataclass
class Candidate:
    """An existing recipe or another draft to compare a draft against; url is already normalized."""

    kind: Literal["recipe", "draft"]
    name: str
    url: str | None
    ingredients: set[str]
    recipe_slug: str | None
    draft_id: UUID4 | None


def normalize_url(url: str) -> str:
    """The link without what does not change the page: https, host in lower case without "www.", no
    fragment, no tracking parameters, the other parameters sorted, no trailing slash."""
    try:
        parts = urlsplit(url.strip() if "//" in url else f"//{url.strip()}")  # "www.example.org/…" is a host too
        host = (parts.hostname or "").removeprefix("www.")
        port = f":{parts.port}" if parts.port and parts.port not in (80, 443) else ""
    except ValueError:  # e.g. a broken IPv6 address; such a link only equals itself
        return url.strip().lower()
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not TRACKING.match(k.lower()))
    return urlunsplit(("https", host + port, parts.path.rstrip("/"), urlencode(query), ""))


def title_key(title: str) -> str:
    """The title's words in lower case and sorted, without filler words and without a final "s"."""
    words = re.findall(r"\w+", title.casefold())
    kept = [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in FILLER_WORDS]
    return " ".join(sorted(kept))


def title_similarity(a: str, b: str) -> float:
    """Similarity of two titles from 0 to 1; untitled ones are never similar."""
    key_a, key_b = title_key(a), title_key(b)
    if not key_a or not key_b:
        return 0.0
    return SequenceMatcher(None, key_a, key_b).ratio()


def ingredient_names(recipe: dict[str, Any]) -> set[str]:
    """The ingredients' names: the parsed food, else the note, without amounts and units."""
    names = set()
    for item in recipe.get("recipeIngredient") or []:
        food = item.get("food")
        text = (food.get("name") if isinstance(food, dict) else None) or item.get("note") or ""
        words = [w for w in re.findall(r"[^\W\d_]+", text.casefold()) if w not in UNITS]
        if words:
            names.add(" ".join(words))
    return names


def ingredient_overlap(a: set[str], b: set[str]) -> float:
    """Share of ingredients the two have in common (Jaccard), 0 if one has none."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def recipe_candidate(recipe: Recipe) -> Candidate:
    """A saved recipe as something to compare against."""
    return Candidate(
        kind="recipe",
        name=recipe.name or "",
        url=normalize_url(recipe.org_url) if recipe.org_url else None,
        ingredients=ingredient_names(recipe.model_dump(mode="json", by_alias=True)),
        recipe_slug=recipe.slug,
        draft_id=None,
    )


def candidates(repos: AllRepositories, exclude_draft: UUID4) -> list[Candidate]:
    """The household's recipes and its other drafts that are not approved yet.
    ponytail: loads every recipe; fine for a family cookbook, a name index is the way up if it grows."""
    found = [recipe_candidate(recipe) for recipe in repos.recipes.get_all()]
    for draft in drafts_repo(repos.session, repos.group_id, repos.household_id).get_all():
        if draft.id == exclude_draft or draft.status == DraftStatus.approved:
            continue
        found.append(
            Candidate(
                kind="draft",
                name=(draft.recipe or {}).get("name") or "",
                url=draft.source_url_normalized,
                ingredients=ingredient_names(draft.recipe or {}),
                recipe_slug=None,
                draft_id=draft.id,
            )
        )
    return found


def match_kind(
    title: str, url: str | None, ingredients: set[str], candidate: Candidate, settings: KhSettings
) -> Literal["duplicate_link", "similar_title", "similar_ingredients"] | None:
    """Why the candidate may be the same dish as the one with this title, normalized url and ingredients, the
    strongest reason first: same link, similar title, or the same ingredients under a halfway similar title. None if
    it is not."""
    if url and candidate.url == url:
        return "duplicate_link"
    similarity = title_similarity(title, candidate.name)
    if similarity >= settings.duplicate_title:
        return "similar_title"
    if (
        similarity >= settings.duplicate_title_with_ingredients
        and ingredient_overlap(ingredients, candidate.ingredients) >= settings.duplicate_ingredients
    ):
        return "similar_ingredients"
    return None


def find_duplicates(
    recipe: dict[str, Any], url: str | None, candidates: list[Candidate], settings: KhSettings
) -> list[DraftWarning]:
    """One hint per candidate that may be the same dish, see match_kind."""
    url_key = normalize_url(url) if url else None
    title = recipe.get("name") or ""
    ingredients = ingredient_names(recipe)
    warnings = []
    for candidate in candidates:
        kind = match_kind(title, url_key, ingredients, candidate, settings)
        if kind:
            warnings.append(
                DraftWarning(
                    kind=kind, name=candidate.name, recipe_slug=candidate.recipe_slug, draft_id=candidate.draft_id
                )
            )
    return warnings
