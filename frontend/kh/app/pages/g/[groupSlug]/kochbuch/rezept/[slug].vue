<!-- KH: the card of one recipe (D43): the same print page as the book with exactly one recipe, no title page and no
table of contents. The servings come from the factor chosen on the recipe page (?servings=); nothing is saved. -->
<template>
  <v-container>
    <h1 class="text-h5 mb-4 d-print-none">
      {{ $t("kh.book.card-title") }}
    </h1>
    <v-progress-linear v-if="loading" indeterminate class="d-print-none" />
    <v-alert v-else-if="!card" type="error" variant="tonal" class="d-print-none">
      {{ $t("kh.book.recipe-not-found") }}
    </v-alert>
    <KhBookEditor
      v-else
      v-model:settings="card.settings"
      v-model:flags="card.flags"
      mode="recipe"
      :recipes="card.recipes"
      :can-save="false"
    />
  </v-container>
</template>

<script setup lang="ts">
import { loadRecipeCard } from "~~/kh/app/composables/use-kh-book";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const route = useRoute();

const loading = ref(true);
const card = ref<Awaited<ReturnType<typeof loadRecipeCard>>>(null);

onMounted(async () => {
  const servings = Number(route.query.servings);
  card.value = await loadRecipeCard(route.params.slug as string, Number.isFinite(servings) && servings > 0 ? servings : null);
  loading.value = false;
});
</script>
