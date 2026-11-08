<!-- KH: the nutrition block under the ingredients (D44, N4): the energy in the header, the table opened, and how far to
trust it: counted ingredients, those left out, whether a suggestion went in, the source. Calculated per serving by
the server (mealie/kh/nutrition); shows nothing when switched off on this device. -->
<template>
  <details v-if="show" class="kh-nutrition d-print-none mt-4 pr-2">
    <template v-if="nutrition">
      <summary class="text-subtitle-1 font-weight-bold">
        {{ $t("kh.nutrition.title") }}<span v-if="headline" class="font-weight-regular"> · {{ headline }}</span>
      </summary>
      <table v-if="nutrition.values" class="kh-nutrition__table my-2">
        <tr v-for="row in NUTRIENT_ROWS" :key="row.key">
          <th scope="row" :class="{ 'pl-4 font-weight-regular': row.dependent }">
            {{ $t(`kh.nutrition.rows.${row.key}`) }}
          </th>
          <td class="text-right">
            {{ formatNutrient(row.key, nutrition.values[row.key], locale) }}
          </td>
        </tr>
      </table>
      <p v-else class="my-2">
        {{ $t("kh.nutrition.title") }}: {{ $t("kh.nutrition.none") }}
      </p>
      <div class="text-caption text-medium-emphasis">
        <p v-if="nutrition.manual">
          {{ $t("kh.nutrition.manual") }}
        </p>
        <template v-else>
          <p v-if="nutrition.total">
            {{ $t("kh.nutrition.counted", { counted: nutrition.counted, total: nutrition.total }) }}
          </p>
          <p v-if="nutrition.missing.length">
            {{ $t("kh.nutrition.missing", { lines: nutrition.missing.join(", ") }) }}
          </p>
          <p v-if="nutrition.estimated">
            <NuxtLink :to="`/g/${groupSlug}/naehrwerte`">
              {{ $t("kh.nutrition.estimated") }}
            </NuxtLink>
          </p>
          <p v-if="nutrition.values">
            {{ $t("kh.nutrition.source") }}
          </p>
        </template>
      </div>
    </template>
    <summary v-else class="text-caption text-medium-emphasis">
      {{ $t("kh.nutrition.failed") }}
    </summary>
  </details>
</template>

<script setup lang="ts">
import { useRequests } from "~/composables/api/api-client";
import { KhNutritionApi, type KhRecipeNutrition } from "../lib/api/nutrition";
import { formatNutrient, NUTRIENT_ROWS, useKhNutritionSetting } from "../lib/nutrition";

const props = defineProps<{ slug: string; groupSlug: string }>();

const { t, locale } = useI18n();
const show = useKhNutritionSetting();
const api = new KhNutritionApi(useRequests());
const nutrition = ref<KhRecipeNutrition | null>(null);

/** "ca. 320 kcal pro Portion", or for the whole recipe when it has no servings; none without an energy value. */
const headline = computed(() => {
  const n = nutrition.value;
  if (!n?.values || n.values.kcal === null) return "";
  const kcal = formatNutrient("kcal", n.values.kcal, locale.value).replace(" kcal", "");
  return t(n.per === "serving" ? "kh.nutrition.kcal-serving" : "kh.nutrition.kcal-recipe", { kcal });
});

// Asks only while the block shows, and again when the switch is turned on or another recipe opens.
watch([() => props.slug, show], async ([slug, shown]) => {
  if (!shown) return;
  const { data } = await api.forRecipe(slug);
  nutrition.value = data ?? null;
}, { immediate: true });
</script>

<style scoped>
.kh-nutrition__table {
  border-collapse: collapse;
  width: 100%;
  max-width: 24rem;
}
.kh-nutrition__table :is(th, td) {
  padding: 2px 0;
  text-align: left;
}
.kh-nutrition__table td {
  text-align: right;
}
</style>
