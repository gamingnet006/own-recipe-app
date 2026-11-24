"""KH: the events that send a push message (D75): a plan entry, a wish, items on a shopping list, a draft ready for
review. Each `notify_*` is cheap and called from a request; the work runs in the background (see sender.dispatch).
A message goes to the people of the household who switched that event on, never to the one who caused it."""

from collections.abc import Callable
from datetime import date

from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.household.shopping_list import ShoppingList
from mealie.db.models.users.users import User
from mealie.kh.i18n.locale import Locale
from mealie.kh.i18n.messages import say
from mealie.kh.notifications import sender
from mealie.kh.notifications.bundle import Bundler
from mealie.kh.notifications.service import recipients
from mealie.schema.household.group_shopping_list import ShoppingListItemOut

WEEKDAYS: dict[Locale, tuple[str, ...]] = {
    "de-DE": ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"),
    "en-US": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
}
PLAN_WINDOW_SECONDS = 2 * 60  # entries planned in a row (a suggested week) go out as one message
SHOPPING_WINDOW_SECONDS = 15 * 60  # at most one message per list in this time
SHOWN_ITEMS = 5

plan_bundles = Bundler(PLAN_WINDOW_SECONDS)
shopping_bundles = Bundler(SHOPPING_WINDOW_SECONDS)


def _name(session: Session, user_id: UUID4, locale: Locale) -> str:
    user = session.get(User, user_id)
    return (user.full_name or user.username) if user else say("someone", locale)


def _group_slug(session: Session, user_id: UUID4) -> str:
    return session.get(User, user_id).group.slug  # type: ignore[union-attr]


def _push(
    session: Session,
    event: str,
    household_id: UUID4,
    actor_id: UUID4 | None,
    text_for: Callable[[Locale], tuple[str, str]],
    path: str,
) -> None:
    """Sends to the household's people who want EVENT, each in their language; PATH may hold {slug} for the group's
    page."""
    users = recipients(session, event, household_id, actor_id)
    if users:
        sender.send_localized(session, users, text_for, path.format(slug=_group_slug(session, users[0])))


def _list(items: list[str]) -> str:
    return ", ".join(items[:SHOWN_ITEMS]) + (" …" if len(items) > SHOWN_ITEMS else "")


# --- plan -------------------------------------------------------------------------------------------------------


def notify_plan_created(actor_id: UUID4, household_id: UUID4, recipe_name: str, day: date) -> None:
    """A meal-plan entry was created (Mealie's route, the wish list, the week suggestion)."""
    item = (recipe_name, day)
    if plan_bundles.add(("plan", household_id, actor_id), (actor_id, household_id), [item]):
        sender.dispatch(_send_plan, actor_id, household_id, [item])


def _plan_item(recipe_name: str, day: date, locale: Locale) -> str:
    """ "Lasagne für Mo 24.11." / "Lasagne for Mon 11/24"."""
    when = f"{WEEKDAYS[locale][day.weekday()]} " + (
        f"{day.day}.{day.month}." if locale == "de-DE" else f"{day.month}/{day.day}"
    )
    return say("push_plan_item", locale, recipe=recipe_name, day=when)


def _send_plan(session: Session, actor_id: UUID4, household_id: UUID4, items: list[tuple[str, date]]) -> None:
    def text_for(locale: Locale) -> tuple[str, str]:
        who, shown = _name(session, actor_id, locale), [_plan_item(name, day, locale) for name, day in items]
        if len(shown) == 1:
            return say("push_plan_title", locale), say("push_plan_one", locale, who=who, item=shown[0])
        return say("push_plan_title", locale), say(
            "push_plan_many", locale, who=who, count=len(shown), items=_list(shown)
        )

    _push(session, "plan", household_id, actor_id, text_for, "/household/mealplan/planner")


# --- wishes -----------------------------------------------------------------------------------------------------


def notify_wish(actor_id: UUID4, household_id: UUID4, recipe_name: str) -> None:
    """Somebody wished a recipe (D72)."""
    sender.dispatch(_send_wish, actor_id, household_id, recipe_name)


def _send_wish(session: Session, actor_id: UUID4, household_id: UUID4, recipe_name: str) -> None:
    def text_for(locale: Locale) -> tuple[str, str]:
        who = _name(session, actor_id, locale)
        return say("push_wish_title", locale), say("push_wish", locale, who=who, recipe=recipe_name)

    _push(session, "wishes", household_id, actor_id, text_for, "/household/mealplan/planner")


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

    def text_for(locale: Locale) -> tuple[str, str]:
        where = (shopping_list.name if shopping_list else None) or say("push_shopping_list", locale)
        who = _name(session, actor_id, locale)
        if len(names) == 1:
            return say("push_shopping_title", locale), say(
                "push_shopping_one", locale, who=who, item=names[0], where=where
            )
        return say("push_shopping_title", locale), say(
            "push_shopping_many", locale, who=who, count=len(names), where=where, items=_list(names)
        )

    _push(session, "shopping", household_id, actor_id, text_for, "/einkauf")


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
    def text_for(locale: Locale) -> tuple[str, str]:
        return say("push_draft_title", locale), say("push_draft", locale, name=name)

    _push(session, "intake", household_id, None, text_for, "/g/{slug}/drafts")
