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
        "fleisch =hack huhn hühn hähnchen haehnchen puten =pute =truthahn =ente enten =gans gänse rinder rindsfilet "
        "schwein =kalb kalbs lamm =wild =hase =reh rehrücken rehkeule rehfilet hirsch schinken speck wurst "
        "würstchen salami bratwurst chorizo =leber leberkäse schmalz =steak =steaks =gulasch =mett "
        "kassler kasseler =gyros roastbeef pancetta prosciutto mortadella pastrami "
        "meat =mince beef pork chicken turkey =duck =goose =lamb mutton =veal venison bacon =ham hamburger sausage "
        "pepperoni brisket sirloin tenderloin meatball =liver gelatin =lard tallow =suet rabbit =quail =oxtail =tripe"
    ).split()
)
# cut out before matching: a tomato, a herb, an egg, fruit and vegetable "flesh", a spice mix, crab meat (that is fish)
NOT_MEAT = (
    "fleischtomate", "fleischkraut", "hühnerei", "fruchtfleisch", "kürbisfleisch", "kokosfleisch", "weizenteig",
    "steakgewürz", "steak-gewürz", "gulaschgewürz", "beefsteak tomato", "beef tomato", "beefsteak", "lamb's lettuce",
    "lamb’s lettuce", "lambs lettuce", "coconut meat", "fruit meat", "nut meat", "walnut meat", "crab meat",
    "crabmeat", "lobster meat", "hirschhornsalz", "wild rice", "wildreis", "wild garlic", "wilder reis",
    "wildkräuter", "wild herbs", "wild salmon", "wildlachs", "wild berries", "wildbeeren", "wild mushroom",
    "wildpilze", "steak seasoning", "steak spice", "cauliflower steak", "tofu steak",
)  # fmt: skip
# a line with one of these is a plant-based product, not meat: "veganes Hack", "Sojahack", "Fleischersatz"
NOT_MEAT_CANCEL = (
    "vegan", "vegetarisch", "veggie", "soja", "ersatz", "pflanzlich", "plant-based", "plant based", "meatless",
    "meat-free", "meat free", "meat substitute", "meat alternative", "tofu", "seitan", "tempeh", "vegetarian",
)  # fmt: skip
# Animal products besides meat, fish, milk and eggs (those the allergen rules know) that make a dish not vegan
ANIMAL_WORDS = ("honig", "=honey")
ANIMAL_ALLERGENS = {"milk", "eggs", "fish", "crustaceans", "molluscs"}
FISH_ALLERGENS = {"fish", "crustaceans", "molluscs"}


def _is_meat(text: str) -> bool:
    """Whether an ingredient text names meat, unless it is plant-based or one of the look-alike words."""
    cleaned = text.lower()
    if any(word in cleaned for word in NOT_MEAT_CANCEL):
        return False
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
