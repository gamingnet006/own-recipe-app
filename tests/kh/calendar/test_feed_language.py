"""KH: the calendar feed is named Kochheft and speaks German unless told otherwise."""

from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from fastapi.testclient import TestClient

from mealie.kh.calendar.translator import FeedTranslator
from mealie.kh.onboarding.models import KhAccountSettings
from mealie.lang import get_locale_provider
from mealie.schema.meal_plan.new_meal import PlanEntryCreate
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser

TOMORROW = datetime.now(UTC).date() + timedelta(days=1)


def feed_for(api_client: TestClient, user: TestUser, params: dict | None = None) -> str:
    """Enables the feed, plans one dinner and returns the unfolded feed text."""
    data = PlanEntryCreate(date=TOMORROW, entry_type="dinner", title=random_string()).model_dump(
        by_alias=True, mode="json"
    )
    assert api_client.post(api_routes.households_mealplans, json=data, headers=user.token).status_code == 201
    token = api_client.post(api_routes.households_mealplans_ical, headers=user.token).json()["mealplanIcalToken"]
    response = api_client.get(api_routes.households_mealplans_ical_token(token), params=params)
    assert response.status_code == 200
    return response.text.replace("\r\n ", "")


def test_german_words_follow_the_app():
    translator = FeedTranslator(get_locale_provider("de-DE"), "de-DE")
    assert translator.t("mealplan.entry-type.dinner") == "Abendessen"
    assert translator.t("mealplan.entry-type.side") == "Beilage"
    assert translator.t("mealplan.entry-type.breakfast") == "Frühstück"


def test_english_words_untouched():
    translator = FeedTranslator(get_locale_provider("en-US"), "en-US")
    assert translator.t("mealplan.entry-type.dinner") == "dinner"


def test_feed_is_named_kochheft(api_client: TestClient, unique_user_fn_scoped: TestUser):
    assert "X-WR-CALNAME:Kochheft – " in feed_for(api_client, unique_user_fn_scoped)


def test_feed_defaults_to_german(api_client: TestClient, unique_user_fn_scoped: TestUser):
    assert "SUMMARY:Abendessen: " in feed_for(api_client, unique_user_fn_scoped)


def test_feed_english_when_asked(api_client: TestClient, unique_user_fn_scoped: TestUser):
    assert "SUMMARY:Dinner: " in feed_for(api_client, unique_user_fn_scoped, {"lang": "en-US"})


def test_feed_follows_the_installation_language_without_a_link_language(
    api_client: TestClient, unique_user_fn_scoped: TestUser, session
):
    settings = session.execute(sa.select(KhAccountSettings)).scalars().first() or KhAccountSettings(session=session)
    settings.locale = "en-US"
    session.add(settings)
    session.commit()
    try:
        assert "SUMMARY:Dinner: " in feed_for(api_client, unique_user_fn_scoped)
        assert "SUMMARY:Abendessen: " in feed_for(api_client, unique_user_fn_scoped, {"lang": "de-DE"})
    finally:
        settings.locale = None
        session.commit()
