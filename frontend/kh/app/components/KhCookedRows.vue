<!-- KH: the start page's two rows "Oft gekocht" and "Lange nicht gekocht" (D67), made of KhRecipeRow; a row
without recipes is not shown, so a new household sees nothing extra. -->
<template>
  <div v-if="rows.length" data-testid="cooked-rows">
    <KhRecipeRow v-for="row in rows" :key="row.key" :title="$t(`kh.cooked.${row.key}`)" :recipes="row.recipes" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { KhCookedApi, type KhCooked } from "../lib/api/cooked";
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
