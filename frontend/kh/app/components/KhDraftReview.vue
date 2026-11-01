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
        <SafeMarkdown :source="step.text" />
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import RecipeYield from "~/components/Domain/Recipe/RecipeYield.vue";
import { useStaticRoutes } from "~/composables/api";
import type { Recipe } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: Recipe }>();

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
</script>
