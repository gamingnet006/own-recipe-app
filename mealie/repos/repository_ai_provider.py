import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import UUID4

from mealie.db.models.group.ai_providers import AIProvider, AIProviderSettings
from mealie.kh.ai.models import KhAiProviderState  # KH: the AI priority list (D39)
from mealie.kh.ai.state import place_last, same_setup, save_state, sync_mealie_roles
from mealie.schema.group.ai_providers import AIProviderCreate, AIProviderOut

from .repository_generic import GroupRepositoryGeneric


class GroupRepositoryAIProvider(GroupRepositoryGeneric[AIProviderOut, AIProvider]):
    def create(self, data: AIProviderCreate | dict):
        if isinstance(data, AIProviderCreate):
            api_key = data.api_key
            data = data.model_dump()
            data["api_key"] = api_key

        if not data.get("api_key"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="API key cannot be empty")

        if not data.get("settings_id"):
            data["settings_id"] = self.session.execute(
                sa.select(AIProviderSettings.id).where(AIProviderSettings.group_id == self.group_id)
            ).scalar_one()

        created = super().create(data)
        # KH: a new provider joins the priority list at the end; the roles follow the list (D39)
        place_last(self.session, created.id, [p.id for p in self.get_all() if p.id != created.id])
        sync_mealie_roles(self.session, self.group_id)
        return created

    def update(self, match_value: str | int | UUID4, new_data: AIProviderCreate | dict):
        if isinstance(new_data, AIProviderCreate):
            # api_key is excluded from the schema's dump, so carry it over by hand, the same
            # way create does. Without this every update looks like it omitted the key.
            api_key = new_data.api_key
            new_data = new_data.model_dump()
            new_data["api_key"] = api_key

        before = self.get_one(match_value)  # KH: to tell a new address, model or key from a new name (D39)

        # Merge existing API key into new data
        if not new_data.get("api_key"):
            existing = self.get_one(match_value)
            if existing:
                new_data["api_key"] = existing.api_key

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
        sync_mealie_roles(self.session, self.group_id)  # KH: the roles follow the priority list (D39)
        return deleted

    def update_many(self, data):
        raise NotImplementedError
