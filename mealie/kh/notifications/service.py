"""KH: "Mitteilungen" (D75): a person's switches and devices, and who gets an event's message."""

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.models.users.users import User
from mealie.kh.notifications.models import KhNotificationSettings, KhPushSubscription
from mealie.kh.notifications.schemas import DEFAULT_EVENING, DEFAULT_ON, EVENTS, NotificationSettings

ALL_OFF = NotificationSettings(
    plan=False, evening=False, shopping=False, wishes=False, intake=False, news=False, evening_time=DEFAULT_EVENING
)
LABELS = (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android"), ("Macintosh", "Mac"), ("Windows", "Windows"))


def device_label(user_agent: str) -> str:
    """A short name for the device list from the browser's name; iPadOS Safari reports "Macintosh" like a Mac."""
    return next((label for marker, label in LABELS if marker in user_agent), "Gerät")


def _row(session: Session, user_id: UUID4) -> KhNotificationSettings | None:
    query = sa.select(KhNotificationSettings).where(KhNotificationSettings.user_id == user_id)
    return session.execute(query).scalar_one_or_none()


def get_settings(session: Session, user_id: UUID4) -> NotificationSettings:
    """The person's choices; all off when they never turned notifications on."""
    row = _row(session, user_id)
    if row is None:
        return ALL_OFF
    return NotificationSettings(
        **{event: bool(row.toggles.get(event)) for event in EVENTS}, evening_time=row.evening_time
    )


def put_settings(session: Session, user_id: UUID4, data: NotificationSettings) -> None:
    """Saves the choices. A changed evening time lets the reminder fire again today if the new time has not passed."""
    row = _row(session, user_id)
    toggles = {event: getattr(data, event) for event in EVENTS}
    if row is None:
        session.add(
            KhNotificationSettings(session=session, user_id=user_id, toggles=toggles, evening_time=data.evening_time)
        )
    else:
        if row.evening_time != data.evening_time:
            row.last_evening = None
        row.toggles = toggles
        row.evening_time = data.evening_time
    session.commit()


def subscribe(session: Session, user_id: UUID4, endpoint: str, p256dh: str, auth: str, user_agent: str) -> None:
    """Saves this device (a known endpoint is taken over by this user). The first device of a person without
    choices switches on the defaults: plan, evening and wishes."""
    row = session.execute(
        sa.select(KhPushSubscription).where(KhPushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    label = device_label(user_agent)
    if row is None:
        session.add(
            KhPushSubscription(
                session=session, user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth, user_agent=label
            )
        )
    else:
        row.user_id, row.p256dh, row.auth, row.user_agent = user_id, p256dh, auth, label
    if _row(session, user_id) is None:
        defaults = {event: event in DEFAULT_ON for event in EVENTS}
        session.add(
            KhNotificationSettings(session=session, user_id=user_id, toggles=defaults, evening_time=DEFAULT_EVENING)
        )
    session.commit()


def unsubscribe(session: Session, user_id: UUID4, endpoint: str) -> None:
    """Removes one of the person's devices; an unknown one is not an error."""
    session.execute(
        sa.delete(KhPushSubscription).where(
            KhPushSubscription.user_id == user_id, KhPushSubscription.endpoint == endpoint
        )
    )
    session.commit()


def devices(session: Session, user_id: UUID4) -> list[KhPushSubscription]:
    """The person's devices, oldest first."""
    return list(
        session.execute(
            sa.select(KhPushSubscription)
            .where(KhPushSubscription.user_id == user_id)
            .order_by(KhPushSubscription.created_at)
        ).scalars()
    )


def delete_user_notifications(session: Session, user_id: UUID4) -> None:
    """Deletes a deleted user's devices and choices; SQLite in Mealie skips cascades. Commits."""
    session.execute(sa.delete(KhPushSubscription).where(KhPushSubscription.user_id == user_id))
    session.execute(sa.delete(KhNotificationSettings).where(KhNotificationSettings.user_id == user_id))
    session.commit()


def recipients(session: Session, event: str, household_id: UUID4, actor_id: UUID4 | None = None) -> list[UUID4]:
    """The users of the household who want EVENT, except the one who caused it."""
    users = sa.select(User.id).where(User.household_id == household_id)
    if actor_id is not None:
        users = users.where(User.id != actor_id)
    wanted = session.execute(
        sa.select(KhNotificationSettings).where(KhNotificationSettings.user_id.in_(users))
    ).scalars()
    return [row.user_id for row in wanted if row.toggles.get(event)]
