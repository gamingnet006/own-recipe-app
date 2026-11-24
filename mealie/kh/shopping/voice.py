"""KH: puts what was said or typed onto a shopping list (D64): "Milch und 2 Butter" becomes two items on the list
named, or on the list used last. Used by the Siri Shortcut, which sends one text with the user's API key."""

import re
from datetime import datetime

from pydantic import UUID4

from mealie.kh.amounts.line import ShoppingLine, parse_shopping_line
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

# "und"/"and" as a word and a comma followed by a space; a decimal comma ("2,5 kg") has no space and stays
ARTICLE_SEPARATOR = re.compile(r"\s+(?:und|and)\s+|,\s+", re.IGNORECASE)


def split_articles(text: str) -> list[str]:
    """The articles said in TEXT, in order: "Milch und 2 Butter, Eier" is Milch, 2 Butter and Eier."""
    return [part.strip() for part in ARTICLE_SEPARATOR.split(text) if part.strip()]


# "bei Rewe", "für Aldi", "auf die dm-Liste", "to the Aldi shopping list" at the end; trailing punctuation is ignored
STORE_TAIL = re.compile(
    r"\s+(?:bei|für|aufs|auf|ins|in|zur|zum|zu|at|for|on|to)"
    r"(?:\s+(?:die|der|den|dem|das|the|my|our|mein(?:e[nmrs]?)?|unser(?:e[nmrs]?)?))?\s+(?P<name>.+?)[\s.!?,;]*$",
    re.IGNORECASE,
)
# what turns a store into a list name when said: "-Liste", " Liste", "-Einkaufsliste", " list", " shopping list"
LIST_WORD = re.compile(r"(?:[\s-]*(?:einkaufs)?liste|\s+(?:shopping\s+)?list|^(?:shopping\s+)?list)$")


# a leading "Setz bitte mir ..." / "please add ..." and a trailing "... drauf" / "... on it" around an article
def _verb_phrase(verbs: str) -> re.Pattern[str]:
    """A leading "bitte/please", one of VERBS and the "mir/uns/bitte/please" after it."""
    return re.compile(rf"^(?:(?:bitte|please)\s+)?(?:{verbs})\s+(?:(?:mir|uns|bitte|please)\s+)*", re.IGNORECASE)


CLEAR_VERB = _verb_phrase("setz|setze|schreib|schreibe|füg|füge|put|add|write")
# "Pack Nudeln" may be a pack of noodles, "Tu"/"Mach" are rare as articles but just as short: stripped only when framed
AMBIGUOUS_VERB = _verb_phrase("pack|packe|mach|mache|tu|tue")
FILLER_TAIL = re.compile(r"(?P<frame>\s+(?:drauf|hinzu|dazu|on it))?[\s.!?]*$", re.IGNORECASE)


def split_frame(clause: str) -> tuple[str, bool]:
    """CLAUSE without a trailing "drauf"/"hinzu"/"dazu"/"on it" and punctuation, and whether such a word was there."""
    tail = FILLER_TAIL.search(clause.strip())
    assert tail  # the pattern matches at the end of any text
    return clause.strip()[: tail.start()].strip(), bool(tail["frame"])


def strip_verb(clause: str, framed: bool) -> str:
    """CLAUSE without a leading "Setz bitte mir": "Setz bitte Butter" is "Butter". The clear verbs always go, the
    ambiguous ones ("Pack", "Mach", "Tu") only when FRAMED (the sentence ends with a frame word or a store)."""
    stripped = CLEAR_VERB.sub("", clause.strip(), count=1)
    return (AMBIGUOUS_VERB.sub("", stripped, count=1) if framed else stripped).strip()


def _list_key(name: str) -> str:
    """A list name for comparing: lower case, without a "Liste", "-Einkaufsliste" or " list" at the end."""
    return LIST_WORD.sub("", name.strip().casefold())


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
        if rest and not found and not spoken:  # "auf die Einkaufsliste": no store named, the default list
            return rest, None
        position = match.start() + 1  # the tail may start at a later preposition ("Milch für Oma bei Rewe")
    return text, None


# spoken amounts: "ein"/"eine"... "zwölf" and "one"... "twelve"; "a"/"an" are no amounts (they may be articles)
NUMBER_WORDS = {
    word: number
    for number, words in enumerate(
        (
            "ein eine einen einem einer eines one",
            "zwei two",
            "drei three",
            "vier four",
            "fünf five",
            "sechs six",
            "sieben seven",
            "acht eight",
            "neun nine",
            "zehn ten",
            "elf eleven",
            "zwölf twelve",
        ),
        start=1,
    )
    for word in words.split()
}
SPOKEN_AMOUNT = re.compile(
    rf"^(?:(?P<word>{'|'.join(NUMBER_WORDS)})(?:[\s-]*mal)?|(?P<twice>twice)|(?P<digits>\d+)\s*(?:-?mal|[x×]|times))\s+",
    re.IGNORECASE,
)


# "ein paar Bananen", "ein bisschen Petersilie", "a couple of bananas": no amount that could be counted
VAGUE_AMOUNT = re.compile(
    r"^(?:(?:ein\s+)?(?:paar|bisschen|wenig)|a\s+(?:couple\s+of|few|bit\s+of|little))\s+(?:von\s+|of\s+)?",
    re.IGNORECASE,
)
# "einen halben Liter Sahne", "eine halbe Gurke" and "half a liter of cream" are half of something
HALF_GERMAN = re.compile(r"^(?:ein\w*\s+)?halb(?:e[nmrs]?)?\s+", re.IGNORECASE)
HALF_ENGLISH = re.compile(r"^half\s+(?:an?\s+)?(?P<unit>\w+)\s+of\s+", re.IGNORECASE)


def spoken_amount_to_digits(article: str) -> str:
    """Turns the amount said at the start of ARTICLE into digits: "Zweimal Butter" is "2 Butter", "3-mal Milch" is
    "3 Milch", "ein Liter Milch" is "1 Liter Milch", "eine halbe Gurke" is "0,5 Gurke". "ein paar Bananen" loses its
    vague amount. "Eier" and a plain "2 Butter" stay as they are."""
    if match := VAGUE_AMOUNT.match(article):
        return article[match.end() :]
    if match := HALF_GERMAN.match(article):
        return f"0,5 {article[match.end() :]}"
    if match := HALF_ENGLISH.match(article):
        return f"0,5 {match['unit']} {article[match.end() :]}"
    match = SPOKEN_AMOUNT.match(article)
    if not match:
        return article
    number = match["digits"] or (2 if match["twice"] else NUMBER_WORDS[match["word"].casefold()])
    return f"{number} {article[match.end() :]}"


def _read_clause(part: str, list_names: list[str]) -> tuple[str, str | None, bool]:
    """One clause as (article, store, framed): the frame word and the store are cut off; "framed" says whether the
    clause ended with a frame word or named a store, which is what lets its verb be stripped."""
    body, has_frame = split_frame(part)
    rest, store = split_store(body, list_names)
    return rest, store, has_frame or rest != body


def plan_additions(text: str, list_names: list[str]) -> list[tuple[str | None, list[str]]]:
    """Splits a spoken TEXT into groups of articles per list, in the order the lists were first said: a clause
    without a store takes the store of the next clause that names one ("Butter und Milch bei Aldi" puts both on
    Aldi), clauses after the last store belong to None, the default list. Pass no LIST_NAMES to ignore stores."""
    read = [_read_clause(part, list_names) for part in split_articles(text)]
    # "Pack Nudeln" may be a pack of noodles: the first clause loses an ambiguous verb only when the sentence ends
    # with a frame word or a store, a later clause only when it does itself
    ends_framed = read[-1][2] if read else False
    clauses = [
        (strip_verb(rest, ends_framed if index == 0 else framed), store)
        for index, (rest, store, framed) in enumerate(read)
    ]
    clauses = [(rest, store) for rest, store in clauses if rest]
    stores: list[str | None] = []
    next_store: str | None = None
    for _, store in reversed(clauses):
        next_store = store or next_store
        stores.insert(0, next_store)
    groups: dict[str | None, list[str]] = {}
    for (article, _), store in zip(clauses, stores, strict=True):
        groups.setdefault(store, []).append(article)
    return list(groups.items())


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


def spoken_summary(results: list[tuple[str, list[str]]]) -> str:
    """What Siri reads out for several lists: one sentence per (list name, article names), in the order given."""
    return " ".join(spoken_confirmation(names, list_name) for list_name, names in results)


def parse_articles(group_repos: AllRepositories, articles: list[str]) -> list[ShoppingLine]:
    """Reads ARTICLES (spoken amounts become digits) without writing any item. GROUP_REPOS is group-scoped. Raises
    ValueError when an article is not understood."""
    ensure_german_units(group_repos)
    matcher = DataMatcher(group_repos)
    return [
        parse_shopping_line(spoken_amount_to_digits(part), matcher.units_by_alias, matcher.foods_by_alias)
        for part in articles
    ]


def add_to_list(
    repos: AllRepositories, group_repos: AllRepositories, shopping_list: ShoppingListOut, lines: list[ShoppingLine]
) -> list[str]:
    """Writes the parsed LINES onto SHOPPING_LIST and returns their names. REPOS is household-scoped (items),
    GROUP_REPOS group-scoped (foods and units)."""
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
