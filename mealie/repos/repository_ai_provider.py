from uuid import UUID

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.db.models.group.ai_providers import AIPromptOverride, AIProvider, AIProviderSettings
from mealie.kh.ai.models import KhAiProviderState  # KH: the AI priority list (D39)
from mealie.kh.ai.state import place_last, same_setup, save_state, sync_mealie_roles
from mealie.schema.group.ai_providers import (
    AIPromptOverrideCreate,
    AIPromptOverrideOut,
    AIProviderCreate,
    AIProviderOut,
)

from .repository_generic import GroupRepositoryGeneric


def _get_settings_id(repo: GroupRepositoryGeneric) -> UUID4:
    return repo.session.execute(
        sa.select(AIProviderSettings.id).where(AIProviderSettings.group_id == repo.group_id)
    ).scalar_one()


class GroupRepositoryAIProvider(GroupRepositoryGeneric[AIProviderOut, AIProvider]):
    def create(self, data: AIProviderCreate | dict):  # type: ignore[override]
        if isinstance(data, AIProviderCreate):
            api_key = data.api_key
            data = data.model_dump()
            data["api_key"] = api_key

        if not data.get("api_key"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="API key cannot be empty")

        if not data.get("settings_id"):
            data["settings_id"] = _get_settings_id(self)

        created = super().create(data)
        # KH: a new provider joins the priority list at the end; the roles follow the list (D39)
        place_last(self.session, created.id, [p.id for p in self.get_all() if p.id != created.id])
        assert isinstance(self.group_id, UUID)  # KH: scoped repositories always carry their group
        sync_mealie_roles(self.session, self.group_id)
        return created

    def update(self, match_value: str | int | UUID4, new_data: AIProviderCreate | dict):  # type: ignore[override]
        if not isinstance(new_data, AIProviderCreate):
            raise TypeError("AI provider updates must be an AIProviderCreate so resolve_update() checks the base URL")

        before = self.get_one(match_value)  # KH: also tells a new address, model or key from a new name (D39)
        if before:
            new_data = before.resolve_update(new_data)

        updated = super().update(match_value, new_data)
        # KH: a saved provider gets another chance in the priority list, e.g. with a new key; with another address,
        # model or key, its last test no longer says whether it reads images (D39)
        forget = {} if before is not None and same_setup(before, updated) else {"supports_images": None}
        save_state(self.session, updated.id, status="ready", paused_until=None, **forget)
        return updated

    def delete(self, value, match_key: str | None = None) -> AIProviderOut:
        # Null out any settings references to this provider before deleting
        self.session.execute(
            sa.update(AIProviderSettings)
            .where(AIProviderSettings.default_provider_id == value)
            .values(default_provider_id=None)
        )
        self.session.execute(
            sa.update(AIProviderSettings)
            .where(AIProviderSettings.audio_provider_id == value)
            .values(audio_provider_id=None)
        )
        self.session.execute(
            sa.update(AIProviderSettings)
            .where(AIProviderSettings.image_provider_id == value)
            .values(image_provider_id=None)
        )

        # KH: the provider's place in the priority list goes with it; SQLite keeps no cascade (D39)
        self.session.execute(sa.delete(KhAiProviderState).where(KhAiProviderState.provider_id == value))

        # Delete
        deleted = super().delete(value, match_key)
        assert isinstance(self.group_id, UUID)  # KH: scoped repositories always carry their group
        sync_mealie_roles(self.session, self.group_id)  # KH: the roles follow the priority list (D39)
        return deleted

    def update_many(self, data):
        raise NotImplementedError


class GroupRepositoryAIPromptOverride(GroupRepositoryGeneric[AIPromptOverrideOut, AIPromptOverride]):
    def create(self, data: AIPromptOverrideCreate | dict):  # type: ignore[override]
        if isinstance(data, AIPromptOverrideCreate):
            data = data.model_dump()

        if not data.get("settings_id"):
            data["settings_id"] = _get_settings_id(self)

        return super().create(data)
