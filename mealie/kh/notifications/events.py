"""KH: the events that send a push message (D75): a plan entry, a wish, items on a shopping list, a draft ready for
review. Each `notify_*` is cheap and called from a request; the work runs in the background (see sender.dispatch).
A message goes to the people of the household who switched that event on, never to the one who caused it."""

from datetime import date

from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.shopping_list import ShoppingList
from mealie.db.models.users.users import User
from mealie.kh.notifications import sender
from mealie.kh.notifications.bundle import Bundler
from mealie.kh.notifications.service import recipients
from mealie.schema.household.group_shopping_list import ShoppingListItemOut

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
PLAN_WINDOW_SECONDS = 2 * 60  # entries planned in a row (a suggested week) go out as one message
SHOPPING_WINDOW_SECONDS = 15 * 60  # at most one message per list in this time
SHOWN_ITEMS = 5

plan_bundles = Bundler(PLAN_WINDOW_SECONDS)
shopping_bundles = Bundler(SHOPPING_WINDOW_SECONDS)


def _name(session: Session, user_id: UUID4) -> str:
    user = session.get(User, user_id)
    return (user.full_name or user.username) if user else "Jemand"


def _group_slug(session: Session, user_id: UUID4) -> str:
    return session.get(User, user_id).group.slug  # type: ignore[union-attr]


def _push(
    session: Session, event: str, household_id: UUID4, actor_id: UUID4 | None, title: str, body: str, path: str
) -> None:
    """Sends to the household's people who want EVENT; PATH may hold {slug} for the group's page."""
    users = recipients(session, event, household_id, actor_id)
    if users:
        sender.send_to_users(session, users, title, body, path.format(slug=_group_slug(session, users[0])))


def _list(items: list[str]) -> str:
    return ", ".join(items[:SHOWN_ITEMS]) + (" …" if len(items) > SHOWN_ITEMS else "")


# --- plan -------------------------------------------------------------------------------------------------------


def notify_plan_created(actor_id: UUID4, household_id: UUID4, recipe_name: str, day: date) -> None:
    """A meal-plan entry was created (Mealie's route, the wish list, the week suggestion)."""
    item = f"{recipe_name} für {WEEKDAYS[day.weekday()]} {day.day}.{day.month}."
    if plan_bundles.add(("plan", household_id, actor_id), (actor_id, household_id), [item]):
        sender.dispatch(_send_plan, actor_id, household_id, [item])


def _send_plan(session: Session, actor_id: UUID4, household_id: UUID4, items: list[str]) -> None:
    who = _name(session, actor_id)
    text = (
        f"{who} hat {items[0]} eingeplant"
        if len(items) == 1
        else f"{who} hat {len(items)} Gerichte eingeplant: {_list(items)}"
    )
    _push(session, "plan", household_id, actor_id, "Essensplan", text, "/household/mealplan/planner")


# --- wishes -----------------------------------------------------------------------------------------------------


def notify_wish(actor_id: UUID4, household_id: UUID4, recipe_name: str) -> None:
    """Somebody wished a recipe (D72)."""
    sender.dispatch(_send_wish, actor_id, household_id, recipe_name)


def _send_wish(session: Session, actor_id: UUID4, household_id: UUID4, recipe_name: str) -> None:
    text = f"{_name(session, actor_id)} wünscht sich {recipe_name}"
    _push(session, "wishes", household_id, actor_id, "Wunschliste", text, "/household/mealplan/planner")


# --- shopping ---------------------------------------------------------------------------------------------------


def notify_items_added(actor_id: UUID4, household_id: UUID4, list_id: UUID4, names: list[str]) -> None:
    """Items were put on a shopping list; more within 15 minutes on the same list go out as one message."""
    names = [name for name in names if name]
    if names and shopping_bundles.add(("shopping", list_id, actor_id), (actor_id, household_id, list_id), names):
        sender.dispatch(_send_items, actor_id, household_id, list_id, names)


def item_names_by_list(items: list[ShoppingListItemOut]) -> dict[UUID4, list[str]]:
    """The names of newly created items per list: the food's name, else the note (typed lines)."""
    names: dict[UUID4, list[str]] = {}
    for item in items:
        names.setdefault(item.shopping_list_id, []).append((item.food.name if item.food else None) or item.note or "")
    return names


def _send_items(session: Session, actor_id: UUID4, household_id: UUID4, list_id: UUID4, names: list[str]) -> None:
    shopping_list = session.get(ShoppingList, list_id)
    where = (shopping_list.name if shopping_list else None) or "die Einkaufsliste"
    who = _name(session, actor_id)
    text = (
        f"{who} hat {names[0]} auf {where} gesetzt"
        if len(names) == 1
        else f"{who} hat {len(names)} Sachen auf {where} gesetzt: {_list(names)}"
    )
    _push(session, "shopping", household_id, actor_id, "Einkaufsliste", text, "/einkauf")


def flush_bundles() -> None:
    """Sends what the bundles held back; run by the scheduler (Mealie's "minutely" jobs run every 5 minutes)."""
    for context, items in plan_bundles.due():
        sender.dispatch(_send_plan, *context, items)  # type: ignore[misc]
    for context, items in shopping_bundles.due():
        sender.dispatch(_send_items, *context, items)  # type: ignore[misc]


# --- intake -----------------------------------------------------------------------------------------------------


def notify_draft_ready(household_id: UUID4, name: str) -> None:
    """A draft has been recognized and waits for review (D35). The submitter is told too: they are who waits for it."""
    sender.dispatch(_send_draft, household_id, name)


def _send_draft(session: Session, household_id: UUID4, name: str) -> None:
    _push(session, "intake", household_id, None, "Eingang", f"Zum Prüfen bereit: {name}", "/g/{slug}/drafts")
