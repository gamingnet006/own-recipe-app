"""KH: what the allergen endpoints send and take (D44), in camelCase like every Mealie answer."""

from typing import Annotated

from pydantic import UUID4, StringConstraints, field_validator

from mealie.schema._mealie import MealieModel

# The 14 EU allergens, in the order the app lists them.
ALLERGENS = (
    "gluten",
    "crustaceans",
    "eggs",
    "fish",
    "peanuts",
    "soy",
    "milk",
    "nuts",
    "celery",
    "mustard",
    "sesame",
    "sulphites",
    "lupin",
    "molluscs",
)


def allergen_key(value: str) -> str:
    """VALUE if it is one of the 14 keys; a ValueError (a 422 answer) otherwise."""
    if value not in ALLERGENS:
        raise ValueError(f"Unknown allergen: {value}")
    return value


class AllergenHit(MealieModel):
    """One allergen of a recipe with the ingredient lines it was found in; corrected says a person's correction
    applies (False: taken out, True: added by hand, None: none)."""

    allergen: str
    lines: list[str]
    corrected: bool | None


class AllergenCorrectionIn(MealieModel):
    """A person's correction of one allergen of one recipe; None removes the correction."""

    present: bool | None


class AllergenProfile(MealieModel):
    """The allergens a user cannot have; stored without duplicates, in the order of ALLERGENS."""

    allergens: list[str]

    @field_validator("allergens")
    @classmethod
    def known_and_ordered(cls, value: list[str]) -> list[str]:
        for key in value:
            allergen_key(key)
        return [key for key in ALLERGENS if key in value]


class AllergenWarning(MealieModel):
    """Members of one household who cannot have an allergen the recipe contains."""

    allergen: str
    names: list[str]


class LineSubstitution(MealieModel):
    """A hint for one ingredient line of a recipe: REPLACEMENT instead of the line's food, because of ALLERGEN."""

    line: str
    allergen: str
    replacement: str


RuleText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SubstitutionIn(MealieModel):
    """A household's own rule: an ingredient text containing MATCH (case does not matter) that has ALLERGEN can be
    replaced by REPLACEMENT."""

    match: RuleText
    replacement: RuleText
    allergen: str

    @field_validator("match")
    @classmethod
    def lowercase(cls, value: str) -> str:
        return value.lower()

    @field_validator("allergen")
    @classmethod
    def known(cls, value: str) -> str:
        return allergen_key(value)


class SubstitutionOut(SubstitutionIn):
    """An own rule as stored."""

    id: UUID4


class VariantIn(MealieModel):
    """The allergens a saved variant of a recipe should be free of."""

    allergens: list[str]

    @field_validator("allergens")
    @classmethod
    def known(cls, value: list[str]) -> list[str]:
        return [allergen_key(key) for key in value]


class VariantOut(MealieModel):
    """The new recipe's slug."""

    slug: str


class AllergenReport(MealieModel):
    """A recipe's allergens, the warnings for the viewer's household and the substitution hints."""

    hits: list[AllergenHit]
    warnings: list[AllergenWarning]
    substitutions: list[LineSubstitution]
