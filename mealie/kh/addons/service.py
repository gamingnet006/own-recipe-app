"""KH: reads, stores and checks the household's add-on switches (D46)."""

import sqlalchemy as sa
from fastapi import Depends, HTTPException, status
from humps import camelize
from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.db.db_setup import generate_session
from mealie.kh.addons.models import KhHouseholdAddons
from mealie.kh.addons.schemas import AddonFlags, AddonsOut
from mealie.kh.features.settings import get_kh_settings
from mealie.repos.all_repositories import AllRepositories
from mealie.schema.response import ErrorResponse

# The name shown in the refusal; the page itself is translated in the frontend
LABELS = {
    "books": "Familienkochbuch",
    "duplicates": "Doppelte Rezepte",
    "nutrition": "Nährwerte",
    "allergens": "Allergene",
    "substitutions": "Austausch und Varianten",
    "whisper": "Audio und Video mit Whisper",
    "telegram": "Telegram-Bot",
    "share_links": "Öffentliche Teilen-Links",
}


def host_unavailable() -> list[str]:
    """The add-ons the host does not offer: the environment is their hard upper limit."""
    settings = get_kh_settings()
    missing = {
        "share_links": not settings.share_links,
        "telegram": not settings.telegram_token or settings.profile == "lokal",  # lokal: nothing leaves the house
        "whisper": not settings.whisper_url,
    }
    return [name for name, gone in missing.items() if gone]


def default_flags() -> AddonFlags:
    """The fresh-install defaults, except that what the host already set up starts on: whoever set a Telegram token,
    Whisper server or share links in the environment keeps them after the update (G5). The Clock button starts on,
    as it always showed wherever the device's own switch is on."""
    settings = get_kh_settings()
    return AddonFlags(
        clock=True,
        share_links=settings.share_links,
        telegram=bool(settings.telegram_token),
        whisper=bool(settings.whisper_url),
    )


def load_flags(session: Session, household_id: UUID4) -> AddonFlags:
    """The household's chosen switches; the defaults while it chose none."""
    row = session.execute(
        sa.select(KhHouseholdAddons).where(KhHouseholdAddons.household_id == household_id)
    ).scalar_one_or_none()
    defaults = default_flags().model_dump()
    return AddonFlags.model_validate({**defaults, **(row.flags if row else {})})


def save_flags(session: Session, household_id: UUID4, flags: AddonFlags) -> None:
    """Stores the household's switches. Commits."""
    row = session.execute(
        sa.select(KhHouseholdAddons).where(KhHouseholdAddons.household_id == household_id)
    ).scalar_one_or_none()
    if row is None:
        session.add(KhHouseholdAddons(session=session, household_id=household_id, flags=flags.model_dump()))
    else:
        row.flags = flags.model_dump()
    session.commit()


def enabled_flags(flags: AddonFlags) -> AddonFlags:
    """What is really in force: a choice the host cannot back is off, and exchange needs allergens."""
    values = flags.model_dump()
    for name in host_unavailable():
        values[name] = False
    values["substitutions"] = values["substitutions"] and values["allergens"]
    return AddonFlags.model_validate(values)


def load_addons(session: Session, household_id: UUID4) -> AddonsOut:
    """The answer of GET /api/kh/addons."""
    flags = load_flags(session, household_id)
    return AddonsOut(
        flags=flags,
        enabled=enabled_flags(flags),
        unavailable=[camelize(name) for name in host_unavailable()],
    )


def addon_enabled(session: Session, household_id: UUID4, name: str) -> bool:
    """Whether the household has the add-on in force."""
    return bool(getattr(enabled_flags(load_flags(session, household_id)), name))


def ensure_addon(session: Session, household_id: UUID4, name: str) -> None:
    """Raises 403 with a readable message while the add-on is off."""
    if not addon_enabled(session, household_id, name):
        label = LABELS.get(name, name)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            ErrorResponse.respond(
                f"{label} ist ausgeschaltet. Ein Admin kann sie unter Mehr → Zusatzfunktionen einschalten."
            ),
        )


def require_household_share_links(token_id: UUID4, session: Session = Depends(generate_session)) -> None:
    """Route dependency for the public shared-recipe page: 404 while the household of the token's recipe has share
    links off. An unknown token passes, the route answers it itself."""
    token = AllRepositories(session, group_id=None, household_id=None).recipe_share_tokens.get_one(token_id)
    if token and not addon_enabled(session, token.recipe.household_id, "share_links"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrorResponse.respond("Share links are switched off"))
