"""KH: sends web push messages (D75). Sending never blocks a request and never raises: jobs run on a small thread
pool, a failure is logged, and a push service that no longer knows a device (404 or 410) loses its subscription."""

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache
from urllib.parse import urlsplit

import requests
import sqlalchemy as sa
from pydantic import UUID4
from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from mealie.core.config import get_app_settings
from mealie.core.root_logger import get_logger
from mealie.db.db_setup import session_context
from mealie.kh.notifications.endpoints import is_push_endpoint
from mealie.kh.notifications.keys import get_vapid
from mealie.kh.notifications.models import KhPushSubscription

logger = get_logger()

GONE = (404, 410)  # the push service no longer knows the device
PUSH_TIMEOUT_SECONDS = 10
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kh-push")


def dispatch(job: Callable[..., None], *args) -> None:
    """Runs JOB(session, *args) in the background with its own session; whatever it raises is logged, not raised.
    Tests replace this with a version that runs the job at once."""
    _pool.submit(run_job, job, *args)


def run_job(job: Callable[..., None], *args) -> None:
    """The body of a background job: own session, errors logged."""
    try:
        with session_context() as session:
            job(session, *args)
    except Exception:
        logger.exception("push job failed")


FALLBACK_SUBJECT = "mailto:kochheft@example.invalid"
RESERVED_SUFFIXES = (".invalid", ".local", ".localhost", ".example", ".test", ".internal")


def vapid_subject(base_url: str) -> tuple[str, bool]:
    """(subject, usable): the contact the push services see. The app's https address when it has one; else a mailto
    with the address' host when that is a real name; else a placeholder (usable False, Apple may refuse it)."""
    parts = urlsplit(base_url)
    host = (parts.hostname or "").lower()
    if parts.scheme == "https" and host:
        return f"https://{host}", True
    if "." in host and not host.endswith(RESERVED_SUFFIXES) and not host.replace(".", "").isdigit():
        return f"mailto:kochheft@{host}", True
    return FALLBACK_SUBJECT, False


@lru_cache
def _subject() -> str:
    """The subject for this installation; warns once when only the placeholder is possible. Mealie's BASE_URL, not
    KH_BASE_URL: compose hands only BASE_URL to this container."""
    subject, usable = vapid_subject(get_app_settings().BASE_URL)
    if not usable:
        logger.warning("BASE_URL is not an https address: push messages to iPhones need one")
    return subject


class _NoRedirectSession(requests.Session):
    """A push service never needs to redirect; following one could lead the server to another address."""

    def get_redirect_target(self, resp):
        return None


def _deliver(subscription: KhPushSubscription, payload: str) -> None:
    """One push call; the only place that talks to a push service, so tests replace it. A stored endpoint outside
    the known push services (an old row) is refused."""
    if not is_push_endpoint(subscription.endpoint):
        raise ValueError("endpoint is not a known push service")
    webpush(
        subscription_info={
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        },
        data=payload,
        vapid_private_key=get_vapid(),
        vapid_claims={"sub": _subject()},
        requests_session=_NoRedirectSession(),
        ttl=24 * 60 * 60,
        timeout=PUSH_TIMEOUT_SECONDS,
    )


def send_to_users(session: Session, user_ids: list[UUID4], title: str, body: str, url: str) -> int:
    """Sends the message to every device of the users; returns how many devices accepted it. A device the push
    service reports as gone is deleted, any other failure is logged."""
    payload = json.dumps({"title": title, "body": body, "url": url})
    rows = (
        session.execute(sa.select(KhPushSubscription).where(KhPushSubscription.user_id.in_(user_ids))).scalars().all()
    )
    sent = 0
    for row in rows:
        try:
            _deliver(row, payload)
        except WebPushException as error:
            status = getattr(error.response, "status_code", None)
            if status in GONE:
                session.delete(row)
            else:
                logger.warning(f"push to a device failed (status {status})")
            continue
        except Exception:
            logger.exception("push to a device failed")
            continue
        row.last_ok_at = datetime.now(UTC).replace(tzinfo=None)
        sent += 1
    session.commit()
    return sent
