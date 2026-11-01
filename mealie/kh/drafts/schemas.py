"""KH: shapes of the drafts API (phase 2), camelCase in JSON like every Mealie answer. The backend sends
codes, never sentences; the frontend turns them into German or English text."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import UUID4, ConfigDict, Field

from mealie.schema._mealie import MealieModel


class DraftStatus(StrEnum):
    """Where a draft stands: being recognized, waiting for review, failed, or saved as a recipe."""

    working = "working"
    ready = "ready"
    failed = "failed"
    approved = "approved"


class DraftSource(StrEnum):
    """What a draft came from; photos and screenshots are both images."""

    link = "link"
    text = "text"
    image = "image"


class DraftError(StrEnum):
    """Why a recognition failed."""

    no_recipe_data = "no_recipe_data"
    ai_not_configured = "ai_not_configured"
    quota_exceeded = "quota_exceeded"
    address_blocked = "address_blocked"
    invalid_result = "invalid_result"
    interrupted = "interrupted"
    unknown = "unknown"


class DraftWarning(MealieModel):
    """A hint for the review: a recipe or another draft this one may duplicate."""

    kind: Literal["duplicate_link", "similar_title", "similar_ingredients"]
    name: str
    recipe_slug: str | None = None
    draft_id: UUID4 | None = None


class DraftOut(MealieModel):
    """A draft as the API returns it; `recipe` is the recognized recipe in Mealie's camelCase form."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    group_id: UUID4
    household_id: UUID4
    user_id: UUID4 | None = None
    user_name: str = ""
    status: DraftStatus
    source_type: DraftSource
    source_url: str | None = None
    source_url_normalized: str | None = None
    source_text: str | None = None
    original_files: list[str] = []
    recipe: dict[str, Any] | None = None
    warnings: list[DraftWarning] = []
    error: DraftError | None = None
    ai_model: str | None = None
    recipe_id: UUID4 | None = None
    approved_by: UUID4 | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    update_at: datetime | None = None


class OriginOut(MealieModel):
    """Where an approved recipe came from, for the badge on the recipe page."""

    draft_id: UUID4
    source_type: DraftSource
    source_url: str | None = None
    user_name: str
    created_at: datetime | None = None
    ai_model: str | None = None
    original_count: int


class ApproveIn(MealieModel):
    """Approve, optionally with servings and yield set in the review. FORCE also approves when the check finds
    possible duplicates that were not there at recognition."""

    force: bool = False
    recipe_servings: float | None = Field(default=None, ge=0)
    recipe_yield_quantity: float | None = Field(default=None, ge=0)
    recipe_yield: str | None = None

    def recipe_changes(self) -> dict[str, Any]:
        """What the review set, under the recipe's own JSON keys."""
        return self.model_dump(by_alias=True, exclude_none=True, exclude={"force"})


class ApproveOut(MealieModel):
    """The saved recipe's slug, so the page can open it."""

    slug: str
