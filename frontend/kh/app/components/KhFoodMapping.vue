<!-- KH: one row of the mapping page (D44, N2): a food, the BLS entry it is matched to, a search in the BLS (waits 300 ms
after the last key), "Bestätigen", "Kein passender Eintrag" and the weight of one piece. -->
<template>
  <v-card variant="outlined" class="pa-4 mb-3">
    <div class="d-flex flex-wrap align-baseline ga-2">
      <span class="text-body-1 font-weight-medium">{{ mapping.foodName }}</span>
      <span class="text-caption text-medium-emphasis">{{ $t("kh.nutrition.page.in-recipes", { count: mapping.recipeCount }, mapping.recipeCount) }}</span>
      <span class="text-caption ml-auto">{{ mapping.confirmed ? $t("kh.nutrition.page.confirmed") : $t("kh.nutrition.page.suggested") }}</span>
    </div>
    <p class="text-body-2 my-2">
      {{ entryName }}
    </p>

    <input v-model="query" type="search" class="kh-mapping__field" :aria-label="$t('kh.nutrition.page.search-label')" :placeholder="$t('kh.nutrition.page.search-label')">
    <ul v-if="hits.length" class="kh-mapping__hits">
      <li v-for="hit in hits" :key="hit.code">
        <v-btn variant="text" block class="justify-start text-none" @click="choose(hit)">
          {{ hit.name }}<span v-if="hit.kcal !== null" class="text-medium-emphasis">&nbsp;· {{ hit.kcal }} kcal</span>
        </v-btn>
      </li>
    </ul>
    <p v-else-if="searched" class="text-caption text-medium-emphasis mt-1">
      {{ $t("kh.nutrition.page.no-hits") }}
    </p>

    <label class="d-block text-caption mt-3">
      {{ $t("kh.nutrition.page.piece-grams") }}
      <input v-model="grams" type="text" inputmode="decimal" class="kh-mapping__field kh-mapping__field--short">
    </label>

    <div class="d-flex flex-wrap ga-2 mt-3">
      <v-btn variant="tonal" color="primary" :disabled="saving" @click="save(chosen?.code ?? mapping.blsCode)">
        {{ $t("kh.nutrition.page.confirm") }}
      </v-btn>
      <v-btn variant="tonal" :disabled="saving" @click="save(null)">
        {{ $t("kh.nutrition.page.no-entry") }}
      </v-btn>
    </div>
    <p v-if="error" class="text-error text-body-2 mt-2" role="alert">
      {{ error }}
    </p>
  </v-card>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import { useRequests } from "~/composables/api/api-client";
import { KhNutritionApi, type KhBlsHit, type KhFoodMapping } from "../lib/api/nutrition";
import { latestRequest } from "../lib/duplicates";
import { parsePieceGrams } from "../lib/nutrition";

/** How long the search waits after the last key. */
const SEARCH_DELAY_MS = 300;

/** The words for the status codes of a failed save. */
const SAVE_ERRORS: Record<number, string> = {
  403: "kh.nutrition.page.forbidden",
  422: "kh.nutrition.page.unknown-code",
};

const props = defineProps<{ mapping: KhFoodMapping }>();
const emit = defineEmits<{ saved: [mapping: KhFoodMapping] }>();

const { t } = useI18n();
const api = new KhNutritionApi(useRequests());
const query = ref("");
const hits = ref<KhBlsHit[]>([]);
const searched = ref(false);
const chosen = ref<KhBlsHit | null>(null);
const grams = ref(props.mapping.pieceGrams?.toString() ?? "");
const saving = ref(false);
const error = ref("");

/** The entry the row stands for: the chosen hit, else the stored or suggested one, else "no matching entry". */
const entryName = computed(() => chosen.value?.name ?? props.mapping.blsName ?? (props.mapping.confirmed ? t("kh.nutrition.page.no-entry") : "–"));

const startRequest = latestRequest();
const search = useDebounceFn(async (text: string) => {
  const isCurrent = startRequest();
  const answer = text.trim() ? await api.searchBls(text.trim()) : null;
  if (!isCurrent()) return;
  // a failed search must not look like "nothing found"
  error.value = answer?.error ? t("kh.nutrition.page.failed") : "";
  hits.value = answer?.data ?? [];
  searched.value = !!answer?.data;
}, SEARCH_DELAY_MS);
watch(query, text => search(text));

function choose(hit: KhBlsHit) {
  chosen.value = hit;
  hits.value = [];
  searched.value = false;
  query.value = "";
}

/** Stores the mapping as confirmed with BLSCODE (null: no matching entry) and the piece weight; the row's owner gets
 * what the server kept. */
async function save(blsCode: string | null) {
  error.value = "";
  const pieceGrams = parsePieceGrams(grams.value);
  if (pieceGrams === "invalid") {
    error.value = t("kh.nutrition.page.failed");
    return;
  }
  saving.value = true;
  const { data, error: failure } = await api.putFood(props.mapping.foodId, { blsCode, confirmed: true, pieceGrams });
  saving.value = false;
  if (data) {
    chosen.value = null; // the saved mapping comes back as the prop; a stale choice must not outlive it
    emit("saved", data);
  }
  else error.value = t(SAVE_ERRORS[failure?.response?.status ?? 0] ?? "kh.nutrition.page.failed");
}
</script>

<style scoped>
.kh-mapping__field {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  padding: 6px 8px;
  width: 100%;
}
.kh-mapping__field--short {
  display: block;
  max-width: 8rem;
}
.kh-mapping__hits {
  list-style: none;
  padding: 0;
}
</style>
