<!-- KH: the allergen block under the ingredients (D44, A1, A2, X1): chips for what the recipe probably contains, the warning
for the household's intolerances with the replacements, "save as variant", and the corrections by hand. Always worded
"probably" and "without guarantee". -->
<template>
  <section v-if="data" class="kh-allergens d-print-none mt-4 pr-2">
    <div v-for="warning in data.warnings" :key="warning.allergen" class="kh-allergens__warning pa-3 mb-2" role="alert">
      <p class="font-weight-bold mb-1">
        {{ warningText(warning) }}
      </p>
      <p v-for="hint in khOn.substitutions ? hintsFor(warning.allergen) : []" :key="hint.line" class="text-body-2 mb-0">
        {{ $t("kh.allergens.instead", { line: hint.line, replacement: hint.replacement }) }}
      </p>
    </div>
    <v-btn
      v-if="data.warnings.length && khOn.substitutions"
      variant="tonal"
      size="small"
      class="mb-2"
      :loading="saving"
      @click="saveVariant"
    >
      {{ $t("kh.allergens.variant") }}
    </v-btn>

    <p class="text-subtitle-2 mb-1">
      {{ data.hits.length ? $t("kh.allergens.contains") : $t("kh.allergens.none-found") }}
    </p>
    <div class="d-flex flex-wrap ga-2">
      <v-chip
        v-for="hit in data.hits"
        :key="hit.allergen"
        :class="['kh-allergens__chip', { 'kh-allergens__chip--out': hit.corrected === false }]"
        :aria-expanded="open === hit.allergen"
        @click="open = open === hit.allergen ? null : hit.allergen"
      >
        {{ $t(`kh.allergens.names.${hit.allergen}`) }}
      </v-chip>
    </div>
    <p class="text-caption text-medium-emphasis mt-1 mb-1">
      {{ $t("kh.allergens.disclaimer") }}
    </p>

    <div v-if="openHit" class="text-body-2 mb-2">
      <p v-if="openHit.corrected === true" class="mb-1">
        {{ $t("kh.allergens.by-hand") }}
      </p>
      <p v-else-if="openHit.corrected === false" class="mb-1">
        {{ $t("kh.allergens.taken-out") }}
      </p>
      <template v-if="openHit.lines.length">
        {{ $t("kh.allergens.from-lines") }}
        <ul class="ml-4">
          <li v-for="line in openHit.lines" :key="line">
            {{ line }}
          </li>
        </ul>
      </template>
      <template v-if="canEdit">
        <v-btn v-if="openHit.corrected === null" size="small" variant="text" @click="correct(openHit.allergen, false)">
          {{ $t("kh.allergens.wrong") }}
        </v-btn>
        <v-btn v-else size="small" variant="text" @click="correct(openHit.allergen, null)">
          {{ $t("kh.allergens.undo") }}
        </v-btn>
      </template>
    </div>

    <select v-if="canEdit" class="kh-allergens__add text-body-2" :aria-label="$t('kh.allergens.add-label')" @change="add">
      <option value="">
        {{ $t("kh.allergens.add") }}
      </option>
      <option v-for="key in addable" :key="key" :value="key">
        {{ $t(`kh.allergens.names.${key}`) }}
      </option>
    </select>
    <p v-if="error" class="text-error text-body-2 mt-2" role="alert">
      {{ error }}
    </p>
  </section>
</template>

<script setup lang="ts">
import { useRequests } from "~/composables/api/api-client";
import { useKhOn } from "../composables/use-kh-addons";
import { refreshKhAllergenWarnings } from "../composables/use-kh-allergens";
import { KH_ALLERGENS, KhAllergensApi, type KhAllergenKey, type KhAllergenWarning, type KhRecipeAllergens } from "../lib/api/allergens";

const props = defineProps<{ slug: string; groupSlug: string; canEdit: boolean }>();

const { t, locale } = useI18n();
const router = useRouter();
const khOn = useKhOn();
const api = new KhAllergensApi(useRequests());
const data = ref<KhRecipeAllergens | null>(null);
const open = ref<KhAllergenKey | null>(null);
const saving = ref(false);
const error = ref("");

const openHit = computed(() => data.value?.hits.find(hit => hit.allergen === open.value));
/** What can still be added: every group that has no chip yet (a struck one is undone instead). */
const addable = computed(() => KH_ALLERGENS.filter(key => !data.value?.hits.some(hit => hit.allergen === key)));

watch(() => props.slug, async (slug) => {
  data.value = (await api.forRecipe(slug)).data ?? null;
}, { immediate: true });

/** "Enthält wahrscheinlich Milch. Lena und Paul vertragen das nicht." */
function warningText(warning: KhAllergenWarning): string {
  const names = new Intl.ListFormat(locale.value, { type: "conjunction" }).format(warning.names);
  return t("kh.allergens.warning", { allergen: t(`kh.allergens.names.${warning.allergen}`), names }, warning.names.length);
}

function hintsFor(allergen: KhAllergenKey) {
  return data.value?.substitutions.filter(hint => hint.allergen === allergen) ?? [];
}

/** Stores a correction (true adds, false takes out, null undoes) and reads the report again, since the PUT answers with
 * the correction only; the marks on the recipe cards follow. */
async function correct(allergen: KhAllergenKey, present: boolean | null) {
  error.value = "";
  const { data: stored } = await api.correct(props.slug, allergen, present);
  const { data: next } = stored ? await api.forRecipe(props.slug) : { data: null };
  if (!next) {
    error.value = t("kh.allergens.failed");
    return;
  }
  data.value = next;
  void refreshKhAllergenWarnings();
}

async function add(event: Event) {
  const select = event.target as HTMLSelectElement;
  const key = select.value as KhAllergenKey | "";
  select.value = "";
  if (key) await correct(key, true);
}

/** Saves a copy without the warned allergens and opens it; 422 means nothing in the lines can be replaced. */
async function saveVariant() {
  error.value = "";
  saving.value = true;
  const { data: created, error: failure } = await api.makeVariant(props.slug, data.value!.warnings.map(w => w.allergen));
  saving.value = false;
  if (created) await router.push(`/g/${props.groupSlug}/r/${created.slug}`);
  else error.value = t(failure?.response?.status === 422 ? "kh.allergens.variant-nothing" : "kh.allergens.failed");
}
</script>

<style scoped>
.kh-allergens__warning {
  border: 1px solid rgb(var(--v-theme-warning));
  border-radius: 8px;
}
.kh-allergens__chip--out {
  text-decoration: line-through;
  opacity: 0.6;
}
.kh-allergens__add {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  padding: 4px 8px;
}
</style>
