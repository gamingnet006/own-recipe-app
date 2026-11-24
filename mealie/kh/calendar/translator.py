"""KH: wraps Mealie's translator so the calendar feed uses the meal-type words the Kochheft frontend shows."""

from mealie.lang.providers import Translator

DEFAULT_FEED_LANG = "de-DE"
"""Language of the feed when the link carries none: Kochheft's household calendars are mostly German"""

# Mealie's backend German differs from its frontend (which Kochheft shows) in these two words only
GERMAN_ENTRY_TYPES = {"mealplan.entry-type.dinner": "Abendessen", "mealplan.entry-type.side": "Beilage"}


class FeedTranslator:
    """Delegates to Mealie's translator; for German it swaps in the words above."""

    def __init__(self, inner: Translator, lang: str) -> None:
        self.inner = inner
        self.lang = lang

    def t(self, key: str, default: str | None = None, **kwargs: object) -> str:
        if self.lang.lower().startswith("de") and key in GERMAN_ENTRY_TYPES:
            return GERMAN_ENTRY_TYPES[key]
        return self.inner.t(key, default, **kwargs)
