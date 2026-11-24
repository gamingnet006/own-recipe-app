from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from mealie.core.security import url_safe_token
from mealie.db.db_setup import generate_session
from mealie.kh.calendar.translator import DEFAULT_FEED_LANG, FeedTranslator  # KH: German feed by default
from mealie.kh.i18n.locale import installation_locale  # KH: the installation's language when the link has none
from mealie.lang import get_locale_provider
from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.permissions import Perm, not_found, require
from mealie.schema.meal_plan.mealplan_ical import MealPlanICalTokenOut
from mealie.services.household_services.mealplan_ical_service import MealPlanICalQuery, MealPlanICalService

router = APIRouter(prefix="/households/mealplans/ical", tags=["Households: Meal Plans"])
# the feed is public, so it can't share the controller's router
public_router = APIRouter(prefix="/households/mealplans/ical", tags=["Households: Meal Plans"])


@controller(router)
class MealplanICalController(BaseUserController):
    def _get_token(self) -> MealPlanICalTokenOut:
        prefs = self.repos.household_preferences.get_one(
            self.household_id, key="household_id", override_schema=MealPlanICalTokenOut
        )
        if not prefs:
            raise not_found("Household not found")
        return prefs

    def _set_token(self, token: str | None) -> MealPlanICalTokenOut:
        self.repos.household_preferences.update(self.household_id, {"mealplan_ical_token": token})
        return self._get_token()

    @router.get("", response_model=MealPlanICalTokenOut)
    def get_ical_token(self):
        """Returns the token for the household's meal plan iCal feed, or null if the feed is disabled"""
        return self._get_token()

    @router.post("", response_model=MealPlanICalTokenOut, dependencies=[require(Perm.HOUSEHOLD_MANAGE)])
    def create_ical_token(self):
        """Enables the meal plan iCal feed, replacing any existing token so old feed URLs stop working"""
        return self._set_token(url_safe_token())

    @router.delete("", response_model=MealPlanICalTokenOut, dependencies=[require(Perm.HOUSEHOLD_MANAGE)])
    def delete_ical_token(self):
        """Disables the meal plan iCal feed"""
        return self._set_token(None)


@public_router.get("/{token}", response_class=Response)
def get_mealplan_ical_feed(
    token: str,
    query: Annotated[MealPlanICalQuery, Query()],
    session: Session = Depends(generate_session),
) -> Response:
    """
    Public iCal feed of the household's meal plan. No authentication is required;
    access is controlled by the secret token in the URL.
    """
    # KH: the link's language (else the installation's, else German) decides the meal-type words, not the calendar
    # app's Accept-Language
    lang = query.lang or installation_locale(session) or DEFAULT_FEED_LANG
    translator = FeedTranslator(get_locale_provider(lang), lang)
    feed = MealPlanICalService(session, translator).get_feed(token, query)
    if feed is None:
        raise not_found("Calendar not found")

    return Response(
        content=feed,
        media_type="text/calendar",
        headers={"Content-Disposition": 'inline; filename="mealplan.ics"', "Cache-Control": "no-cache"},
    )
