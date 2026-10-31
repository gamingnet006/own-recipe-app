<!-- KH: the recipe recognized from a draft (phase 2): name, servings, times, ingredients and steps. The steps
go through Mealie's SafeMarkdown; nothing from a draft is put into the page as raw HTML. -->
<template>
  <div>
    <h3 class="text-h5 mb-2">
      {{ recipe.name }}
    </h3>
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
import type { Recipe } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: Recipe }>();

const i18n = useI18n();

const facts = computed(() => [
  { label: i18n.t("recipe.servings"), value: props.recipe.recipeServings },
  { label: i18n.t("recipe.yield"), value: props.recipe.recipeYield },
  { label: i18n.t("recipe.total-time"), value: props.recipe.totalTime },
  { label: i18n.t("recipe.prep-time"), value: props.recipe.prepTime },
  { label: i18n.t("recipe.perform-time"), value: props.recipe.performTime },
].filter(fact => fact.value));
</script>
