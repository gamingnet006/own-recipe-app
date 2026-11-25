// KH: a recipe as plain text (D61), for messages, notes, files and the cookbook export. Kochheft reads this format
// back without AI (D62): the labels here are the ones mealie/kh/drafts/text_format.py looks for; keep both in sync.
import { scaleTitle } from "./amounts";
import { recipeTimes, scaleBase } from "../composables/use-kh-recipe";
import type { RecipeIngredient, RecipeOut, RecipeStep } from "~/lib/api/types/recipe";

/** The words an export is written in, per language. The import (mealie/kh/drafts/text_format.py) reads both sets, so
 * old German exports and new English ones work; keep the two in sync. The signature is the last line of every export
 * and how the import knows the text is ours. */
const LABELS = {
  "de-DE": {
    servings: "Portionen", ingredients: "Zutaten", steps: "Zubereitung", notes: "Notizen", familyNote: "Unsere Notiz",
    source: "Quelle", signature: "Exportiert aus Kochheft", times: { prep: "Vorbereitung", perform: "Zubereitung", total: "Gesamt" },
  },
  "en-US": {
    servings: "Servings", ingredients: "Ingredients", steps: "Instructions", notes: "Notes", familyNote: "Our note",
    source: "Source", signature: "Exported from Cookbook", times: { prep: "Prep time", perform: "Cook time", total: "Total time" },
  },
} as const;

/** The labels of the language of LOCALE; anything but English is German, as before. */
const labelsFor = (locale: string) => (locale.startsWith("en") ? LABELS["en-US"] : LABELS["de-DE"]);

/** How the views write an ingredient line and a step at SCALE (amounts scaled, no markup); the callers bring Mealie's
 * own display in, which only works while a component is set up (see use-kh-recipe-text.ts). */
export interface TextReaders {
  ingredient: (line: RecipeIngredient, scale: number) => string;
  step: (place: number, step: RecipeStep, scale: number) => string;
}

/** TEXT on one line: a line break would end an ingredient or a step for the reader. */
function oneLine(text: string): string {
  return text.replace(/\s*\n\s*/g, " ").trim();
}

/** The line under the title: servings (with the yield word the page shows, "13 Muffins") and times, only those the
 * recipe has. */
function infoLine(recipe: RecipeOut, scale: number, locale: string): string {
  const labels = labelsFor(locale);
  const base = scaleBase(recipe);
  const count = new Intl.NumberFormat(locale, { maximumFractionDigits: 1, useGrouping: false }).format(base * scale);
  const word = recipe.recipeYieldQuantity ? (recipe.recipeYield ?? "").trim() : "";
  const servings = base ? [`${labels.servings}: ${[count, word].filter(Boolean).join(" ")}`] : [];
  const times = recipeTimes(recipe, locale).map(time => `${labels.times[time.key]}: ${time.value}`);
  return [...servings, ...times].join(" · ");
}

/** RECIPE at SCALE as text: title, info line, "Zutaten:" with "- " lines, "Zubereitung:" with numbered steps, optional
 * "Notizen:", "Unsere Notiz:" (the household's note, D82, FAMILY_NOTE) and "Quelle:", then the signature (in English
 * "Ingredients:", "Instructions:", "Notes:", "Our note:", "Source:", "Exported from Cookbook"). Section titles stand on a line of their own; amounts in the ingredients,
 * the titles and the steps scale. LOCALE writes the numbers and times. */
export function recipeText(recipe: RecipeOut, scale: number, locale: string, read: TextReaders, familyNote = ""): string {
  const labels = labelsFor(locale);
  const ingredients = (recipe.recipeIngredient ?? []).flatMap((line) => {
    const text = oneLine(read.ingredient(line, scale));
    return [...(line.title ? [oneLine(scaleTitle(line.title, scale, locale))] : []), ...(text ? [`- ${text}`] : [])];
  });
  let number = 0;
  const steps = (recipe.recipeInstructions ?? []).flatMap((step, place) => {
    const text = oneLine(read.step(place, step, scale));
    return text ? [...(step.title ? [oneLine(step.title)] : []), `${++number}. ${text}`] : [];
  });
  const notes = (recipe.notes ?? []).map(note => [note.title, note.text].filter(Boolean).join("\n").trim()).filter(Boolean);
  return [
    [recipe.name, infoLine(recipe, scale, locale)].filter(Boolean).join("\n"),
    [`${labels.ingredients}:`, ...ingredients].join("\n"),
    [`${labels.steps}:`, ...steps].join("\n"),
    notes.length ? `${labels.notes}:\n${notes.join("\n\n")}` : "",
    familyNote.trim() ? `${labels.familyNote}: ${oneLine(familyNote)}` : "",
    recipe.orgURL ? `${labels.source}: ${oneLine(recipe.orgURL)}` : "",
    labels.signature,
  ].filter(Boolean).join("\n\n") + "\n";
}

/** The file ending for a photo of the media type TYPE ("image/jpeg" → "jpg"); webp when the server names none. */
export function photoExtension(type: string | null): string {
  const kind = (type ?? "").split(";")[0]!.split("/")[1]?.trim();
  return !kind ? "webp" : kind === "jpeg" ? "jpg" : kind;
}
