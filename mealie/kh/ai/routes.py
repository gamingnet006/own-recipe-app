"""KH: the AI list's routes under /api/kh/ai (D39): managers read and set the providers' order, every member of the
group may ask whether any AI is available."""

from dataclasses import asdict

from fastapi import HTTPException, status

from mealie.db.models._model_utils.datetime import get_utc_now
from mealie.kh.ai.chain import candidates
from mealie.kh.ai.schemas import AiStatusOut, OrderIn, ProviderStateOut
from mealie.kh.ai.state import in_order, load_states, save_state, sync_mealie_roles
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter
from mealie.schema.response import ErrorResponse

router = UserAPIRouter(prefix="/ai")


@controller(router)
class KhAiController(BaseUserController):
    """The priority list of the user's group."""

    def _listed(self) -> list[ProviderStateOut]:
        """The group's providers in the list's order, with their state."""
        providers = self.repos.group_ai_providers.get_all()
        states = load_states(self.session, [p.id for p in providers])
        return [
            ProviderStateOut(provider_id=p.id, name=p.name, model=p.model, **asdict(states[p.id]))
            for p in in_order(providers, states)
        ]

    @router.get("/providers", response_model=list[ProviderStateOut])
    def providers(self) -> list[ProviderStateOut]:
        """The providers in order, for whoever manages them."""
        self.checks.can_manage()
        return self._listed()

    @router.put("/providers/order", response_model=list[ProviderStateOut])
    def set_order(self, data: OrderIn) -> list[ProviderStateOut]:
        """Sets the order; it must name every provider of the group exactly once. Mealie's default and image
        provider follow it."""
        self.checks.can_manage()
        known = {p.id for p in self.repos.group_ai_providers.get_all()}
        if len(data.provider_ids) != len(set(data.provider_ids)) or set(data.provider_ids) != known:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                ErrorResponse.respond("The order must name every provider of the group exactly once"),
            )
        for position, provider_id in enumerate(data.provider_ids):
            save_state(self.session, provider_id, position=position)
        sync_mealie_roles(self.session, self.group_id)
        return self._listed()

    @router.get("/status", response_model=AiStatusOut)
    def ai_status(self) -> AiStatusOut:
        """Whether any provider can take a request now, and whether there is one at all, for the intake's hint."""
        providers = self.repos.group_ai_providers.get_all()
        states = load_states(self.session, [p.id for p in providers])
        available = bool(candidates(providers, states, images=False, now=get_utc_now()))
        return AiStatusOut(available=available, configured=bool(providers))
