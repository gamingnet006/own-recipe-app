"""KH: tag suggestions without AI: "schnell", "vegetarisch"/"vegan", "mit Fleisch"/"mit Fisch" from a recipe's times
and ingredient lines. Pure functions; the fish and animal-product words come from the allergen rules (D44), only
the meat words are added here."""

from mealie.kh.allergens.rules import allergens_of_line, line_text, text_has
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut

QUICK_MAX_SECONDS = 30 * 60  # the starter tag "schnell (bis 30 Min.)"

# Words for meat in ingredient texts, German and English; matched like the allergen words (substring, or a whole
# word with a leading "="). Plain "fleisch" is a substring, so Hackfleisch and Fleischbrühe count.
MEAT_WORDS = tuple(
    (
        "fleisch =hack huhn hühn hähnchen haehnchen puten =pute =truthahn =ente =gans rinder =rind schwein "
        "=kalb kalbs lamm =wild =hase schinken speck wurst würstchen salami bratwurst =bacon chorizo =leber "
        "gelatine schmalz =chicken =beef =pork =ham =sausage =lamb =turkey "
    ).split()
)
NOT_MEAT = ("fleischtomate", "fleischkraut", "hühnerei")  # cut out before matching: a tomato, a herb and an egg
# Animal products besides meat, fish, milk and eggs (those the allergen rules know) that make a dish not vegan
ANIMAL_WORDS = ("honig", "=honey")
ANIMAL_ALLERGENS = {"milk", "eggs", "fish", "crustaceans", "molluscs"}
FISH_ALLERGENS = {"fish", "crustaceans", "molluscs"}


def _is_meat(text: str) -> bool:
    cleaned = text.lower()
    for word in NOT_MEAT:
        cleaned = cleaned.replace(word, " ")
    return any(text_has(cleaned, word) for word in MEAT_WORDS)


def _seconds(recipe: RecipeDraft | RecipeOut) -> int | None:
    """The total time, else preparation plus cooking; None when the recipe gives no time."""
    if recipe.total_time_seconds:
        return recipe.total_time_seconds
    return (recipe.prep_time_seconds or 0) + (recipe.perform_time_seconds or 0) or None


def suggested_keys(recipe: RecipeDraft | RecipeOut) -> set[str]:
    """The starter-tag keys the rules would give the recipe. The diet tags need ingredient lines: a recipe without
    any is not called vegetarian just because nothing was found."""
    keys: set[str] = set()
    seconds = _seconds(recipe)
    if seconds is not None and seconds <= QUICK_MAX_SECONDS:
        keys.add("quick")
    texts = [line_text(line)[1] for line in recipe.recipe_ingredient]
    if not any(texts):
        return keys
    allergens = set().union(*(allergens_of_line(text) for text in texts))
    meat = any(_is_meat(text) for text in texts)
    fish = bool(allergens & FISH_ALLERGENS)
    animal = bool(allergens & ANIMAL_ALLERGENS) or any(text_has(text, word) for text in texts for word in ANIMAL_WORDS)
    if meat:
        keys.add("meat")
    if fish:
        keys.add("fish")
    if not meat and not fish:
        keys.add("vegetarian")
        if not animal:
            keys.add("vegan")
    return keys
