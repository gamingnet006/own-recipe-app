<!-- KH: the recipe recognized from a draft (phase 2): picture, name, yield, servings, times, ingredients and steps.
Steps go through Mealie's SafeMarkdown and the yield through Mealie's RecipeYield, which let no markup from a
draft run; nothing else from a draft is put into the page as HTML. -->
<template>
  <div>
    <v-img
      v-if="image"
      :src="image"
      max-height="260"
      cover
      rounded
      class="mb-3"
    />
    <h3 class="text-h5 mb-2">
      {{ recipe.name }}
    </h3>
    <RecipeYield
      v-if="recipe.recipeYieldQuantity || recipe.recipeYield"
      :yield-quantity="recipe.recipeYieldQuantity ?? 0"
      :yield-text="recipe.recipeYield ?? ''"
      class="mb-2"
    />
    <div v-if="facts.length" class="d-flex flex-wrap ga-2 mb-4">
      <v-chip v-for="fact in facts" :key="fact.label" size="small" variant="tonal">
        {{ fact.label }}: {{ fact.value }}
      </v-chip>
    </div>
    <h4 class="text-subtitle-1 font-weight-bold">
      {{ $t("recipe.ingredients") }}
    </h4>
    <ul class="mb-4 ml-5">
      <li v-for="(ingredient, index) in recipe.recipeIngredient" :key="index">
        {{ ingredient.display || ingredient.note }}
      </li>
    </ul>
    <h4 class="text-subtitle-1 font-weight-bold">
      {{ $t("recipe.instructions") }}
    </h4>
    <ol class="ml-5">
      <li v-for="(step, index) in recipe.recipeInstructions" :key="index" class="mb-2">
        <!-- a step with linked amounts (D39): tapping one unlinks or links it again -->
        <p v-if="stepParts[index]">
          <template v-for="(part, n) in stepParts[index]" :key="n">
            <button
              v-if="part.index !== null"
              type="button"
              class="kh-amount"
              :class="{ 'kh-amount--on': isLinked(part.index) }"
              :aria-pressed="isLinked(part.index)"
              :disabled="!linked"
              @click="toggle(part.index)"
            >
              {{ part.text }}
            </button>
            <template v-else>
              {{ part.text }}
            </template>
          </template>
        </p>
        <SafeMarkdown v-else :source="step.text" />
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import RecipeYield from "~/components/Domain/Recipe/RecipeYield.vue";
import { useStaticRoutes } from "~/composables/api";
import type { Recipe } from "~/lib/api/types/recipe";
import { draftAmounts } from "../composables/use-kh-drafts";
import { stepSegments } from "../lib/amounts";

const props = defineProps<{ recipe: Recipe }>();
// the indices of the step links that stay linked; without it the review only shows them
const linked = defineModel<number[]>("linked");

const i18n = useI18n();
const { recipeImage } = useStaticRoutes();

// The picture the recognition took from a page; a photo draft shows its own photo as the original instead
const image = computed(() => (props.recipe.id && props.recipe.image ? recipeImage(props.recipe.id, props.recipe.image) : undefined));

const facts = computed(() => [
  { label: i18n.t("recipe.servings"), value: props.recipe.recipeServings },
  { label: i18n.t("recipe.total-time"), value: props.recipe.totalTime },
  { label: i18n.t("recipe.prep-time"), value: props.recipe.prepTime },
  { label: i18n.t("recipe.perform-time"), value: props.recipe.performTime },
].filter(fact => fact.value));

const links = computed(() => draftAmounts(props.recipe).stepAmounts);
// each step's text in pieces, with the links' indices in the draft; null for a step without links
const stepParts = computed(() =>
  (props.recipe.recipeInstructions ?? []).map((step, place) => {
    const own = links.value.map((link, index) => ({ ...link, index })).filter(link => link.step === place);
    if (!own.length) return null;
    return stepSegments(step.text ?? "", own).map(part => ({
      text: part.text,
      index: part.link === null ? null : own[part.link]!.index,
    }));
  }),
);

/** Whether the link at INDEX stays linked: as the review set it, else as the recognition found it. */
function isLinked(index: number): boolean {
  return linked.value ? linked.value.includes(index) : !!links.value[index]?.linked;
}

/** Unlinks a linked place, or links it again. */
function toggle(index: number) {
  if (!linked.value) return;
  linked.value = isLinked(index) ? linked.value.filter(i => i !== index) : [...linked.value, index];
}
</script>

<style scoped>
/* KH: a linked amount reads as text with a tint; an unlinked one is underlined with dots (D39) */
.kh-amount {
  background: none;
  border: 0;
  border-radius: 4px;
  color: inherit;
  font: inherit;
  margin: 0;
  padding: 0 2px;
  text-decoration: underline dotted;
  text-underline-offset: 3px;
  cursor: pointer;
}
.kh-amount--on {
  background: rgba(var(--v-theme-primary), 0.16);
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}
.kh-amount:disabled {
  cursor: default;
}
</style>
