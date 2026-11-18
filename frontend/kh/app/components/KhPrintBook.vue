<!-- KH: the family cookbook's page (D43): a title page, a table of contents and one sheet per recipe. It is both the
live preview in the editor and the printout, so what the preview shows is what the print dialog prints. -->
<template>
  <div v-if="entries.length" class="kh-print" :class="{ 'kh-preview': preview }">
    <section v-if="settings.titlePage" class="kh-sheet kh-title-page">
      <h1>{{ settings.title }}</h1>
      <p v-if="settings.subtitle">
        {{ settings.subtitle }}
      </p>
    </section>

    <section v-if="settings.toc" class="kh-sheet kh-toc">
      <h2>{{ $t("kh.book.toc") }}</h2>
      <ol>
        <li v-for="entry in entries" :key="entry.recipe.id">
          {{ $t("kh.book.number", { n: entry.number }) }} {{ entry.recipe.name }}
        </li>
      </ol>
    </section>

    <article v-for="entry in entries" :key="entry.recipe.id" class="kh-sheet kh-recipe">
      <h2>
        <span v-if="entries.length > 1" class="kh-nr">{{ $t("kh.book.number", { n: entry.number }) }}</span>
        {{ entry.recipe.name }}
      </h2>
      <p class="kh-meta">
        <span v-if="entry.servings">{{ entry.servings }} {{ $t("kh.recipe.servings", entry.servings) }}</span>
        <span v-for="time in recipeTimes(entry.recipe, $i18n.locale)" :key="time.key">
          {{ $t(`recipe.${time.key}-time`) }}: {{ time.value }}
        </span>
      </p>
      <SafeMarkdown v-if="settings.description && entry.recipe.description" :source="entry.recipe.description" />
      <img v-if="entry.photo" class="kh-photo" :src="recipeImage(entry.recipe.id, entry.recipe.image)" alt="">

      <div class="kh-columns">
        <div class="kh-ingredients">
          <h3>{{ $t("recipe.ingredients") }}</h3>
          <template v-for="(line, index) in entry.recipe.recipeIngredient ?? []" :key="index">
            <h4 v-if="line.title" class="kh-group">
              {{ scaleTitle(line.title, scaleOf(entry), $i18n.locale) }}
            </h4>
            <p class="kh-line">
              <SafeInlineHtml :html="ingredientText(line, scaleOf(entry))" />
            </p>
          </template>
        </div>
        <div class="kh-steps">
          <h3>{{ $t("recipe.instructions") }}</h3>
          <div v-for="(step, index) in entry.recipe.recipeInstructions ?? []" :key="index" class="kh-step">
            <h4 v-if="step.title" class="kh-group">
              {{ step.title }}
            </h4>
            <SafeMarkdown :source="khStepDisplay(index, step, entry.recipe, scaleOf(entry), oven).html" />
          </div>
        </div>
      </div>

      <div v-if="settings.notes && entry.recipe.notes?.length" class="kh-notes">
        <h3>{{ $t("recipe.notes") }}</h3>
        <div v-for="(note, index) in entry.recipe.notes" :key="index">
          <h4 v-if="note.title" class="kh-group">
            {{ note.title }}
          </h4>
          <SafeMarkdown :source="note.text" />
        </div>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { recipeTimes } from "../composables/use-kh-recipe";
import { scaleTitle } from "../lib/amounts";
import type { KhBookSettings } from "../lib/api/books";
import type { BookEntry } from "../lib/book";
import type { Oven } from "../lib/oven";
import { khStepDisplay } from "../lib/step-text";
import { useStaticRoutes } from "~/composables/api";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

defineProps<{
  settings: KhBookSettings;
  entries: BookEntry[];
  /** The oven of the printing device for the temperature brackets; null leaves them out. */
  oven: Oven | null;
  /** On screen as white A4 sheets instead of the printout. */
  preview: boolean;
}>();

const { recipeImage } = useStaticRoutes();
const { parseIngredientText } = useIngredientTextParser();

/** Mealie's scale for the entry's servings: the recipe page scales its ingredients the same way. */
function scaleOf(entry: BookEntry): number {
  return entry.recipe.recipeServings ? entry.servings / entry.recipe.recipeServings : 1;
}

/** The ingredient line at SCALE as Mealie writes it; since Mealie 3.31 it is raw text, cleaned by <SafeInlineHtml>. */
function ingredientText(line: RecipeIngredient, scale: number): string {
  return parseIngredientText(line, scale, false);
}
</script>
