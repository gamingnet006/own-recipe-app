"""KH: what the AI list's routes send and take (D39), in camelCase like every Mealie answer."""

from datetime import datetime

from pydantic import UUID4

from mealie.schema._mealie import MealieModel


class ProviderStateOut(MealieModel):
    """A provider with its place in the list and its state, for the AI settings."""

    provider_id: UUID4
    name: str
    model: str
    position: int
    status: str
    paused_until: datetime | None = None
    supports_images: bool | None = None


class OrderIn(MealieModel):
    """The group's providers in their new order, each exactly once."""

    provider_ids: list[UUID4]


class AiStatusOut(MealieModel):
    """Whether any provider can take a request now, and whether the group has one at all; all a family member
    learns."""

    available: bool
    configured: bool
