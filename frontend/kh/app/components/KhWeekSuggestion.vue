<!-- KH: "Woche vorschlagen" (D70): a dialog on the meal planner with one suggested dinner per day that has none yet.
     Each row can be swapped ("Anderes", which asks for one more recipe with the shown ones left out) or unticked;
     "Übernehmen" creates the ticked dinner entries. -->
<template>
  <v-dialog v-model="open" max-width="560" scrollable>
    <v-card :title="$t('kh.week-suggestion.title')">
      <v-card-text>
        <p v-if="loading" class="text-medium-emphasis">
          {{ $t("kh.week-suggestion.loading") }}
        </p>
        <p v-else-if="!rows.length" class="text-medium-emphasis" data-testid="week-suggestion-empty">
          {{ $t("kh.week-suggestion.none") }}
        </p>
        <div v-for="(row, i) in rows" :key="row.date" class="d-flex align-center ga-3 mb-3" data-testid="week-suggestion-row">
          <v-checkbox-btn v-model="row.checked" :aria-label="$t('kh.week-suggestion.take')" />
          <v-img
            :src="imageOf(row.recipe)"
            width="64"
            height="64"
            cover
            rounded
            class="flex-grow-0"
          />
          <div class="flex-grow-1" style="min-width: 0">
            <div class="text-caption text-medium-emphasis">
              {{ $d(parseISO(row.date), "short") }}
            </div>
            <NuxtLink :to="`/g/${groupSlug}/r/${row.recipe.slug}`" target="_blank" class="text-body-1 font-weight-medium">
              {{ row.recipe.name }}
            </NuxtLink>
          </div>
          <v-btn variant="text" size="small" @click="swap(i)">
            {{ $t("kh.week-suggestion.other") }}
          </v-btn>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="open = false">
          {{ $t("general.cancel") }}
        </v-btn>
        <v-btn color="primary" variant="flat" :disabled="!ticked" :loading="saving" @click="apply">
          {{ $t("kh.week-suggestion.apply") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { parseISO } from "date-fns";
import { KhWeekSuggestionApi, type KhSuggestedRecipe } from "../lib/api/week-suggestion";
import { buildRows, daysWithoutDinner, entriesToCreate, type PlannedMeal, type SuggestionRow } from "../lib/week-suggestion";
import { useUserApi } from "~/composables/api";
import { useRequests } from "~/composables/api/api-client";
import { useStaticRoutes } from "~/composables/api/static-routes";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

const props = defineProps<{ days: Date[]; meals: PlannedMeal[] }>();
/** COUNT dinners were created; the planner reloads and offers the shopping list. */
const emit = defineEmits<{ planned: [count: number] }>();
const open = defineModel<boolean>({ default: false });

const { recipeSmallImage } = useStaticRoutes();
const groupSlug = useMealieAuth().user.value?.groupSlug;
const i18n = useGlobalI18n();
const suggestions = new KhWeekSuggestionApi(useRequests());
const rows = ref<SuggestionRow[]>([]);
const loading = ref(false);
const saving = ref(false);
const ticked = computed(() => rows.value.some(row => row.checked));

function imageOf(recipe: KhSuggestedRecipe) {
  return recipeSmallImage(recipe.id, recipe.image ?? "");
}

// every opening starts from a fresh suggestion for the days that are free now
watch(open, async (isOpen) => {
  if (!isOpen) return;
  const dates = daysWithoutDinner(props.days, props.meals);
  rows.value = [];
  if (!dates.length) return;
  loading.value = true;
  const { data } = await suggestions.get(dates.length, []);
  loading.value = false;
  rows.value = buildRows(dates, data ?? []);
});

/** Replaces the recipe of row I by a new one that is none of the shown recipes. */
async function swap(i: number) {
  const { data } = await suggestions.get(1, rows.value.map(row => row.recipe.id));
  const next = data?.[0];
  if (next) rows.value[i]!.recipe = next;
  else alert.info(i18n.t("kh.week-suggestion.no-more"));
}

async function apply() {
  const api = useUserApi();
  saving.value = true;
  const entries = entriesToCreate(rows.value);
  const results = await Promise.all(entries.map(entry => api.mealplans.createOne(entry)));
  saving.value = false;
  const created = results.filter(result => result.data).length;
  if (created < entries.length) alert.error(i18n.t("events.something-went-wrong"));
  open.value = false;
  if (created) emit("planned", created);
}
</script>
