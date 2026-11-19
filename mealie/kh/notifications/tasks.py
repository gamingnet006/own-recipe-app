"""KH: what the scheduler does every few minutes for "Mitteilungen" (D75): sends what the bundles held back, the evening
reminders whose time has come, and the news message once after an update."""

from datetime import date, datetime, time, timedelta
from pathlib import Path

import sqlalchemy as sa
from dateutil.tz import tzlocal
from sqlalchemy.orm import Session

from mealie.core.config import get_app_dirs
from mealie.core.root_logger import get_logger
from mealie.db.db_setup import session_context
from mealie.db.models.household.mealplan import GroupMealPlan
from mealie.db.models.users.users import User
from mealie.kh.notifications import sender
from mealie.kh.notifications.events import flush_bundles
from mealie.kh.notifications.hints import PlannedRecipe, evening_message
from mealie.kh.notifications.models import KhNotificationSettings, KhPushSubscription
from mealie.kh.onboarding.news import NEWS_VERSION

logger = get_logger()


def _planned(session: Session, household_id, day) -> list[PlannedRecipe]:
    """The household's plan entries of DAY as what the reminder needs; entries without a recipe count by their title."""
    entries = session.execute(
        sa.select(GroupMealPlan)
        .join(User, GroupMealPlan.user_id == User.id)
        .where(User.household_id == household_id, GroupMealPlan.date == day)
        .order_by(GroupMealPlan.created_at)
    ).scalars()
    out = []
    for entry in entries:
        recipe = entry.recipe
        if recipe is None:
            out.append(PlannedRecipe(name=entry.title))
            continue
        foods = [
            (i.food.name or "", i.food.label.name if i.food.label else None) for i in recipe.recipe_ingredient if i.food
        ]
        out.append(
            PlannedRecipe(name=recipe.name or "", foods=foods, steps=[s.text or "" for s in recipe.recipe_instructions])
        )
    return out


# The scheduler's "minutely" jobs run every 5 minutes, so a reminder set for 23:58 is first seen after midnight.
# A reminder for a day stays due until that day ends, and for 10 more minutes past midnight.
LATE_GRACE = timedelta(minutes=10)


def _due_day(row: KhNotificationSettings, now: datetime) -> date | None:
    """The day whose reminder is due now and not yet sent: today, or yesterday while it is at most LATE_GRACE past
    its time. None when nothing is due."""
    hour, minute = (int(part) for part in row.evening_time.split(":"))
    for day in (now.date() - timedelta(days=1), now.date()):
        moment = datetime.combine(day, time(hour, minute), tzinfo=now.tzinfo)
        recent = day == now.date() or now - moment <= LATE_GRACE
        if moment <= now and recent and row.last_evening != day.isoformat():
            return day
    return None


def send_due_evenings(session: Session, now: datetime) -> int:
    """Sends the evening reminder ("tomorrow" of its day) to everyone whose time has come and who has not had it for
    that day; returns how many were sent. A person with nothing planned gets nothing and is not asked again."""
    has_device = sa.exists().where(KhPushSubscription.user_id == KhNotificationSettings.user_id)
    rows = session.execute(sa.select(KhNotificationSettings).where(has_device)).scalars()
    sent = 0
    for row in rows:
        # the switch sits in a JSON column
        if not row.toggles.get("evening") or (day := _due_day(row, now)) is None:
            continue
        row.last_evening = day.isoformat()
        user = session.get(User, row.user_id)
        message = evening_message(_planned(session, user.household_id, day + timedelta(days=1))) if user else None
        if message:
            sent += sender.send_to_users(session, [row.user_id], message[0], message[1], "/household/mealplan/planner")
    session.commit()
    return sent


def _news_marker() -> Path:
    return get_app_dirs().DATA_DIR / "kh" / "news-pushed"


def send_news_once(session: Session) -> int:
    """After an update with new "Neu in Kochheft" cards, tells everyone who switched the news on, once: the version
    last announced is kept in the data folder. Returns how many people were reached."""
    marker = _news_marker()
    if marker.exists() and marker.read_text().strip() == NEWS_VERSION:
        return 0
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(NEWS_VERSION)
    wanted = [
        row.user_id for row in session.execute(sa.select(KhNotificationSettings)).scalars() if row.toggles.get("news")
    ]
    if not wanted:
        return 0
    return sender.send_to_users(
        session, wanted, f"Neu in Kochheft {NEWS_VERSION}", "Schau dir die Neuigkeiten an.", "/"
    )


def run_notifications() -> None:
    """The scheduler's "minutely" job (every 5 minutes); each part is guarded, so one failure stops no other."""
    flush_bundles()
    for part in (lambda s: send_due_evenings(s, datetime.now(tzlocal())), send_news_once):
        try:
            with session_context() as session:
                part(session)
        except Exception:
            logger.exception("notification task failed")
