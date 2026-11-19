<!-- KH: the start page's two rows "Oft gekocht" and "Lange nicht gekocht" (D67), made of Mealie's recipe cards; a row
without recipes is not shown, so a new household sees nothing extra. -->
<template>
  <div v-if="rows.length" data-testid="cooked-rows">
    <section v-for="row in rows" :key="row.key" class="mb-4">
      <h2 class="text-h6 mb-2">
        {{ $t(`kh.cooked.${row.key}`) }}
      </h2>
      <div class="d-flex ga-3 overflow-x-auto pb-2 kh-cooked-row">
        <RecipeCard
          v-for="recipe in row.recipes"
          :key="recipe.id"
          class="kh-cooked-card"
          :name="recipe.name"
          :slug="recipe.slug"
          :recipe-id="recipe.id"
          :image="recipe.image ?? undefined"
          :image-height="120"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { KhCookedApi, type KhCooked } from "../lib/api/cooked";
import RecipeCard from "~/components/Domain/Recipe/RecipeCard.vue";
import { useRequests } from "~/composables/api/api-client";

const cooked = ref<KhCooked | null>(null);
const rows = computed(() => [
  { key: "often", recipes: cooked.value?.often ?? [] },
  { key: "long-ago", recipes: cooked.value?.longAgo ?? [] },
].filter(row => row.recipes.length));

// a failed request just leaves the rows out: they are a nicety, not part of the page
onMounted(async () => {
  const { data } = await new KhCookedApi(useRequests()).get();
  cooked.value = data;
});
</script>

<style scoped>
.kh-cooked-card {
  flex: 0 0 180px;
}
</style>
