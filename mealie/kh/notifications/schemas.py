"""KH: the data of "Mitteilungen" (D75): a device's push subscription, the person's choices, and the device list."""

import re
from datetime import datetime

from pydantic import UUID4, ConfigDict, Field, field_validator

from mealie.kh.notifications.endpoints import is_push_endpoint
from mealie.schema._mealie import MealieModel

EVENTS = ("plan", "evening", "shopping", "wishes", "intake", "news")
DEFAULT_ON = ("plan", "evening", "wishes")  # what turning notifications on switches on; the rest stays off
DEFAULT_EVENING = "18:00"
TIME_PATTERN = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


class SubscriptionKeys(MealieModel):
    p256dh: str = Field(max_length=200)
    auth: str = Field(max_length=100)


class SubscriptionIn(MealieModel):
    """What the browser's PushSubscription.toJSON() gives."""

    endpoint: str = Field(max_length=2000)
    keys: SubscriptionKeys

    @field_validator("endpoint")
    @classmethod
    def only_https(cls, value: str) -> str:
        """Only the known push services: anything else could make the server call an arbitrary address (SSRF)."""
        if not is_push_endpoint(value):
            raise ValueError("endpoint is not a known push service")
        return value


class SubscriptionOut(MealieModel):
    id: UUID4
    endpoint: str
    user_agent: str
    created_at: datetime | None = None
    last_ok_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationSettings(MealieModel):
    """The six switches and the time of the evening reminder."""

    plan: bool
    evening: bool
    shopping: bool
    wishes: bool
    intake: bool
    news: bool
    evening_time: str = DEFAULT_EVENING

    @field_validator("evening_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        if not TIME_PATTERN.fullmatch(value):
            raise ValueError("evening_time must be HH:MM")
        return value
