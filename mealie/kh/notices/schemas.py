"""KH: what the bell's routes send (D39): notices as kind and values, worded by the frontend in the reader's
language, and how many are unread."""

from datetime import datetime

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class NoticeOut(MealieModel):
    """One notice, e.g. kind "ai_quota" for "Gemini" until 9:00 with "Groq" next."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    kind: str
    provider: str | None = None
    next_provider: str | None = None
    until: datetime | None = None
    created_at: datetime


class NoticesOut(MealieModel):
    """The group's newest notices and how many of them came after the user last opened the bell."""

    items: list[NoticeOut]
    unread: int
