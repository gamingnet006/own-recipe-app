<!-- KH: the mapping page "Mehr → Nährwerte" (D44, N2): every food used in recipes and the BLS entry it is matched to, the
open ones (suggestions nobody confirmed) on top. A mapping applies to all recipes of the group. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.nutrition") }}
      </template>
      {{ $t("kh.nutrition.page.description") }}
    </BasePageTitle>

    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-else-if="failed" type="error" variant="tonal">
      {{ $t("kh.nutrition.page.failed") }}
    </v-alert>
    <p v-else-if="!foods.length" class="text-center text-medium-emphasis py-8">
      {{ $t("kh.nutrition.page.empty") }}
    </p>

    <template v-if="foods.length">
      <h2 class="text-subtitle-1 font-weight-bold mb-2">
        {{ $t("kh.nutrition.page.open", { count: openCount }) }}
      </h2>
      <p v-if="!openCount" class="text-medium-emphasis mb-4">
        {{ $t("kh.nutrition.page.none-open") }}
      </p>
      <KhFoodMapping v-for="food in sorted" :key="food.foodId" :mapping="food" @saved="replace" />
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { useRequests } from "~/composables/api/api-client";
import { KhNutritionApi, type KhFoodMapping as Mapping } from "~~/kh/app/lib/api/nutrition";
import { openFirst } from "~~/kh/app/lib/nutrition";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const api = new KhNutritionApi(useRequests());
const foods = ref<Mapping[]>([]);
const loading = ref(true);
const failed = ref(false);

const sorted = computed(() => openFirst(foods.value));
const openCount = computed(() => foods.value.filter(food => !food.confirmed).length);

onMounted(async () => {
  const { data } = await api.getFoods();
  failed.value = !data;
  foods.value = data ?? [];
  loading.value = false;
});

/** Puts what the server kept in the place of the row, so the row moves to the confirmed ones. */
function replace(saved: Mapping) {
  foods.value = foods.value.map(food => (food.foodId === saved.foodId ? saved : food));
}
</script>
