<!-- KH: one row of Mealie's recipe cards that scrolls sideways, with a heading; the cooked rows (D67) and the season row
(D80) use it. -->
<template>
  <section class="kh-recipe-row mb-4">
    <h2 class="text-h6 mb-2">
      {{ title }}
    </h2>
    <div class="d-flex ga-3 overflow-x-auto pb-2">
      <RecipeCard
        v-for="recipe in recipes"
        :key="recipe.id"
        class="kh-row-card"
        :name="recipe.name"
        :slug="recipe.slug"
        :recipe-id="recipe.id"
        :image="recipe.image ?? undefined"
        :image-height="120"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import RecipeCard from "~/components/Domain/Recipe/RecipeCard.vue";

defineProps<{
  title: string;
  recipes: { id: string; slug: string; name: string; image: string | null }[];
}>();
</script>

<style scoped>
/* the start page has no side padding of its own: keep heading and cards off the screen edge */
.kh-recipe-row {
  padding-inline: 16px;
  padding-top: 12px;
}

.kh-row-card {
  flex: 0 0 180px;
}
</style>
