"""KH: the drafts repository: Mealie's household repository over kh_drafts, so every query sees only the
given group and household, like Mealie's own household data."""

from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.schemas import DraftOut
from mealie.repos._utils import NotSet
from mealie.repos.repository_generic import HouseholdRepositoryGeneric


def drafts_repo(
    session: Session, group_id: UUID4 | NotSet | None, household_id: UUID4 | NotSet | None
) -> HouseholdRepositoryGeneric[DraftOut, KhDraft]:
    """Drafts of one household; None for both reaches every draft, which only the cleanup needs."""
    return HouseholdRepositoryGeneric(session, "id", KhDraft, DraftOut, group_id=group_id, household_id=household_id)
