"""KH: puts what was said or typed onto a shopping list (D64): "Milch und 2 Butter" becomes two items on the list
named, or on the list used last. Used by the Siri Shortcut, which sends one text with the user's API key."""

import re
from datetime import datetime

from pydantic import UUID4

from mealie.kh.amounts.line import parse_shopping_line
from mealie.kh.amounts.parse import ensure_german_units
from mealie.kh.shopping.service import ensure_food, ensure_unit
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.household.group_shopping_list import (
    ShoppingListItemCreate,
    ShoppingListItemOut,
    ShoppingListItemUpdateBulk,
    ShoppingListOut,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.services.household_services.shopping_lists import ShoppingListService
from mealie.services.parser_services._base import DataMatcher

# "und" as a word and a comma followed by a space; a decimal comma ("2,5 kg") has no space and stays
ARTICLE_SEPARATOR = re.compile(r"\s+und\s+|,\s+", re.IGNORECASE)


def split_articles(text: str) -> list[str]:
    """The articles said in TEXT, in order: "Milch und 2 Butter, Eier" is Milch, 2 Butter and Eier."""
    return [part.strip() for part in ARTICLE_SEPARATOR.split(text) if part.strip()]


# "bei Rewe", "für Aldi", "auf die dm-Liste" at the end; trailing punctuation is ignored
STORE_TAIL = re.compile(
    r"\s+(?:bei|für|auf|in|zu)(?:\s+(?:die|der|den|dem))?\s+(?P<name>.+?)(?:\s+Liste|-Liste)?[\s.!?,;]*$", re.IGNORECASE
)


def _list_key(name: str) -> str:
    """A list name for comparing: lower case, without a "Liste" or "-Liste" at the end."""
    return re.sub(r"[\s-]*liste$", "", name.strip().casefold())


def split_store(text: str, list_names: list[str]) -> tuple[str, str | None]:
    """Finds the store said at the end of TEXT ("Milch bei Rewe") when it names one of LIST_NAMES: returns the text
    without that tail and the list's name. The exact name wins over a longer one ("Rewe" before "Rewe City"), else a
    unique prefix is taken ("Rossmann" for "Rossmann Innenstadt"). Anything else ("Kaffee für Gäste") stays as said."""
    position = 0
    while match := STORE_TAIL.search(text, position):
        rest, spoken = text[: match.start()].strip(), _list_key(match["name"])
        keys = {name: _list_key(name) for name in list_names}
        found = [name for name, key in keys.items() if key == spoken] or [
            name for name, key in keys.items() if spoken and key.startswith(f"{spoken} ")
        ]
        if rest and len(found) == 1:
            return rest, found[0]
        position = match.start() + 1  # the tail may start at a later preposition ("Milch für Oma bei Rewe")
    return text, None


def pick_list(lists: list[ShoppingListOut], name: str | None) -> ShoppingListOut | None:
    """The list called NAME (ignoring case), else the one updated most recently; None when there is none (or when
    NAME is given and no list has it)."""
    if name:
        return next((entry for entry in lists if (entry.name or "").casefold() == name.strip().casefold()), None)
    # the database's timestamps are naive, so datetime.min is comparable
    return max(lists, key=lambda entry: entry.updated_at or entry.created_at or datetime.min, default=None)  # noqa: DTZ901


def spoken_confirmation(names: list[str], list_name: str) -> str:
    """The German sentence Siri reads out: "Milch, Butter und Eier stehen auf der Liste Rewe." """
    what = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} und {names[-1]}"
    verb = "steht" if len(names) == 1 else "stehen"
    return f"{what} {verb} auf der Liste {list_name}."


def add_to_list(
    repos: AllRepositories, group_repos: AllRepositories, shopping_list: ShoppingListOut, text: str
) -> list[str]:
    """Writes each article of TEXT onto SHOPPING_LIST and returns their names. REPOS is household-scoped (items),
    GROUP_REPOS group-scoped (foods and units). Raises ValueError when no article is understood."""
    ensure_german_units(group_repos)
    matcher = DataMatcher(group_repos)
    lines = [parse_shopping_line(part, matcher.units_by_alias, matcher.foods_by_alias) for part in split_articles(text)]
    service = ShoppingListService(repos)
    names: list[str] = []
    for line in lines:
        food = line.food or ensure_food(group_repos, line.name, None)
        unit = line.unit or (ensure_unit(group_repos, line.unit_abbreviation) if line.unit_abbreviation else None)
        there = _item_of(repos, shopping_list, food.id)
        if there:
            # open first, else ticked off: it goes (back) on the list; an amount said replaces the old one with its unit
            changes: dict = {"checked": False}
            if line.quantity:
                changes |= {"quantity": line.quantity, "unit_id": unit.id if unit else None, "unit": unit}
                changes["note"] = line.note or there.note
            service.bulk_update_items([there.cast(ShoppingListItemUpdateBulk, **changes)])
        else:
            service.bulk_create_items(
                [
                    ShoppingListItemCreate(
                        shopping_list_id=shopping_list.id,
                        food_id=food.id,
                        unit_id=unit.id if unit else None,
                        note=line.note,
                        quantity=line.quantity or 0,
                    )
                ]
            )
        names.append(food.name)
    return names


def _item_of(repos: AllRepositories, shopping_list: ShoppingListOut, food_id: UUID4) -> ShoppingListItemOut | None:
    """The item of this food on the list: an open one, else a ticked-off one, else None."""
    query = PaginationQuery(per_page=-1, query_filter=f"shopping_list_id={shopping_list.id} AND food_id={food_id}")
    items = repos.group_shopping_list_item.page_all(query).items
    return min(items, key=lambda item: item.checked, default=None)
