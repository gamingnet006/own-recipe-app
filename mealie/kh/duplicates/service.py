"""KH: the duplicate report over a household's recipes and the ignored pairs (D43). The comparison is the draft
check's (mealie/kh/drafts/duplicates.py)."""

from itertools import combinations

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.drafts.duplicates import match_kind, recipe_candidate, title_similarity
from mealie.kh.duplicates.models import KhDuplicateIgnored
from mealie.kh.duplicates.schemas import DUPLICATE_REPORT_LIMIT, DuplicatePair, RecipeRef
from mealie.kh.features.settings import KhSettings
from mealie.schema.recipe.recipe import Recipe


def sorted_pair(a: UUID4, b: UUID4) -> tuple[UUID4, UUID4]:
    """The two IDs in the order the ignored pairs are stored in: the smaller as a string first."""
    return (a, b) if str(a) < str(b) else (b, a)


def ignore_pair(session: Session, group_id: UUID4, a: UUID4, b: UUID4) -> None:
    """Remembers that both recipes are kept, so the report skips the pair; a pair already ignored stays one row.
    Commits."""
    first, second = sorted_pair(a, b)
    known = session.execute(
        sa.select(KhDuplicateIgnored.id).where(
            KhDuplicateIgnored.recipe_a == first, KhDuplicateIgnored.recipe_b == second
        )
    ).first()
    if known is None:
        session.add(KhDuplicateIgnored(session=session, group_id=group_id, recipe_a=first, recipe_b=second))
    session.commit()


def delete_ignored(session: Session, recipe_ids: list[UUID4]) -> None:
    """Deletes the ignored pairs of deleted recipes; SQLite in Mealie checks no foreign keys, so the cascade is not
    enough. Commits."""
    session.execute(
        sa.delete(KhDuplicateIgnored).where(
            KhDuplicateIgnored.recipe_a.in_(recipe_ids) | KhDuplicateIgnored.recipe_b.in_(recipe_ids)
        )
    )
    session.commit()


def duplicate_report(
    session: Session, recipes: list[Recipe], tag_id: UUID4 | None, settings: KhSettings
) -> list[DuplicatePair]:
    """Pairs of RECIPES that may be the same dish, the most alike first, at most DUPLICATE_REPORT_LIMIT; without the
    ignored pairs, and with TAG_ID only those where at least one has that tag."""
    ignored = {
        (str(row.recipe_a), str(row.recipe_b))
        for row in session.execute(sa.select(KhDuplicateIgnored.recipe_a, KhDuplicateIgnored.recipe_b))
    }
    prepared = [(recipe, recipe_candidate(recipe)) for recipe in recipes]
    pairs = []
    # ponytail: compares every pair (n²/2); fine for a family cookbook, a title index if it grows
    for (first, first_candidate), (second, second_candidate) in combinations(prepared, 2):
        if tag_id and not any(tag.id == tag_id for recipe in (first, second) for tag in recipe.tags or []):
            continue
        if tuple(map(str, sorted_pair(first.id, second.id))) in ignored:
            continue
        kind = match_kind(
            first.name or "", first_candidate.url, first_candidate.ingredients, second_candidate, settings
        )
        if kind:
            similarity = 1.0 if kind == "duplicate_link" else title_similarity(first.name or "", second.name or "")
            pairs.append(DuplicatePair(a=ref(first), b=ref(second), kind=kind, similarity=similarity))
    pairs.sort(key=lambda pair: pair.similarity, reverse=True)
    return pairs[:DUPLICATE_REPORT_LIMIT]


def ref(recipe: Recipe) -> RecipeRef:
    """The recipe as a report shows it."""
    return RecipeRef(
        slug=recipe.slug or "", name=recipe.name or "", org_url=recipe.org_url, tags=[t.name for t in recipe.tags or []]
    )
