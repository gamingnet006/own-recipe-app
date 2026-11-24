"""KH: tests for the table of server sentences: both languages everywhere, same placeholders, texts per language."""

import re

from mealie.kh.i18n.messages import MESSAGES, say
from mealie.kh.notifications.hints import PlannedRecipe, evening_message
from mealie.kh.speakable import speakable_message


def test_every_sentence_exists_in_both_languages_with_the_same_placeholders():
    for key, texts in MESSAGES.items():
        assert set(texts) == {"de-DE", "en-US"}, key
        assert all(texts.values()), key
        assert {lang: set(re.findall(r"{(\w+)}", text)) for lang, text in texts.items()}["de-DE"] == set(
            re.findall(r"{(\w+)}", texts["en-US"])
        ), key


def test_say_fills_in_values_and_defaults_to_german():
    assert say("push_wish", "en-US", who="Anna", recipe="Soup") == "Anna wishes for Soup"
    assert say("push_wish", who="Anna", recipe="Suppe") == "Anna wünscht sich Suppe"


def test_error_sentences_follow_the_language():
    assert speakable_message(404, {}, "de-DE") == "Das gibt es nicht."
    assert speakable_message(404, {}, "en-US") == "That does not exist."
    assert speakable_message(500, None, "en-US") == "That did not work."
    assert speakable_message(400, {"code": "empty"}, "en-US") == "There is nothing in it."
    assert speakable_message(422, {"message": "as sent"}, "en-US") == "as sent"


def test_the_evening_reminder_in_english():
    recipe = PlannedRecipe("Lasagne", foods=[("Mince", "Meat")], steps=["Soak the beans overnight. Then cook."])
    assert evening_message([recipe], "en-US") == (
        "Tomorrow: Lasagne",
        "Remember to thaw: Mince\nPrepare the day before: Soak the beans overnight",
    )
