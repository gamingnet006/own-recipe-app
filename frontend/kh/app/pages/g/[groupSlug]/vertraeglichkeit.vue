<!-- KH: the page "Mehr → Ich vertrage nicht" (D44, A2, X1): which of the 14 allergen groups this account does not tolerate,
and the household's own substitution rules (ingredient, replacement, allergen) that go before the standard list. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.allergens.profile.title") }}
      </template>
      {{ $t("kh.allergens.profile.description") }}
    </BasePageTitle>

    <v-progress-linear v-if="loading" indeterminate />
    <div v-else class="mb-6">
      <v-checkbox
        v-for="key in KH_ALLERGENS"
        :key="key"
        :model-value="selected.includes(key)"
        :label="$t(`kh.allergens.names.${key}`)"
        color="primary"
        density="compact"
        hide-details
        @update:model-value="toggle(key, !!$event)"
      />
    </div>

    <template v-if="khOn.substitutions">
      <h2 class="text-subtitle-1 font-weight-bold mb-1">
        {{ $t("kh.allergens.profile.rules-title") }}
      </h2>
      <p class="text-body-2 text-medium-emphasis mb-2">
        {{ $t("kh.allergens.profile.rules-description") }}
      </p>
      <p v-if="!rules.length" class="text-medium-emphasis mb-2">
        {{ $t("kh.allergens.profile.rules-none") }}
      </p>
      <v-list v-else rounded="lg" class="py-0 mb-2">
        <v-list-item v-for="rule in rules" :key="rule.id">
          {{ $t("kh.allergens.profile.rule", { match: rule.match, replacement: rule.replacement, allergen: $t(`kh.allergens.names.${rule.allergen}`) }) }}
          <template #append>
            <v-btn
              icon
              variant="text"
              size="small"
              :aria-label="$t('kh.allergens.profile.rule-delete', { match: rule.match })"
              @click="removeRule(rule.id)"
            >
              <v-icon>{{ $globals.icons.delete }}</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>

      <form class="d-flex flex-wrap ga-2 align-start" @submit.prevent="addRule">
        <v-text-field v-model="match" :label="$t('kh.allergens.profile.match')" density="compact" hide-details style="min-width: 10rem" />
        <v-text-field v-model="replacement" :label="$t('kh.allergens.profile.replacement')" density="compact" hide-details style="min-width: 10rem" />
        <v-select
          v-model="allergen"
          :items="allergenItems"
          :label="$t('kh.allergens.profile.allergen')"
          density="compact"
          hide-details
          style="min-width: 10rem"
        />
        <v-btn type="submit" variant="tonal" color="primary" :disabled="!match.trim() || !replacement.trim() || !allergen">
          {{ $t("kh.allergens.profile.rule-add") }}
        </v-btn>
      </form>
    </template>
    <p v-if="message" class="text-body-2 mt-3" :class="{ 'text-error': failed }" role="status">
      {{ message }}
    </p>
  </v-container>
</template>

<script setup lang="ts">
import { refreshKhAllergenWarnings } from "~~/kh/app/composables/use-kh-allergens";
import { KH_ALLERGENS, KhAllergensApi, type KhAllergenKey, type KhSubstitutionRule } from "~~/kh/app/lib/api/allergens";
import { useKhOn } from "~~/kh/app/composables/use-kh-addons";
import { useRequests } from "~/composables/api/api-client";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const { t } = useI18n();
const khOn = useKhOn();
const api = new KhAllergensApi(useRequests());
const selected = ref<KhAllergenKey[]>([]);
const rules = ref<KhSubstitutionRule[]>([]);
const loading = ref(true);
const message = ref("");
const failed = ref(false);
const match = ref("");
const replacement = ref("");
const allergen = ref<KhAllergenKey | null>(null);

const allergenItems = computed(() => KH_ALLERGENS.map(key => ({ title: t(`kh.allergens.names.${key}`), value: key })));

onMounted(async () => {
  const [mine, own] = await Promise.all([
    api.getAllergies(),
    khOn.value.substitutions ? api.getRules() : Promise.resolve({ data: [] as KhSubstitutionRule[] }), // KH: D46
  ]);
  selected.value = mine.data?.allergens ?? [];
  rules.value = own.data ?? [];
  if (!mine.data || !own.data) report(false, "kh.allergens.profile.failed");
  loading.value = false;
});

/** Shows the result of the last change under the form. */
function report(ok: boolean, key: string) {
  failed.value = !ok;
  message.value = t(key);
}

/** Stores the profile with KEY ticked or unticked; the marks on the recipe cards follow. A failure puts the box back. */
async function toggle(key: KhAllergenKey, on: boolean) {
  const before = selected.value;
  selected.value = KH_ALLERGENS.filter(k => (k === key ? on : before.includes(k)));
  const { data } = await api.putAllergies(selected.value);
  if (data) {
    selected.value = data.allergens;
    report(true, "kh.allergens.profile.saved");
    void refreshKhAllergenWarnings();
  }
  else {
    selected.value = before;
    report(false, "kh.allergens.profile.failed");
  }
}

async function addRule() {
  if (!allergen.value) return;
  const { data } = await api.addRule({ match: match.value.trim(), replacement: replacement.value.trim(), allergen: allergen.value });
  if (data) {
    rules.value = [...rules.value, data];
    match.value = "";
    replacement.value = "";
    allergen.value = null;
    report(true, "kh.allergens.profile.saved");
  }
  else report(false, "kh.allergens.profile.failed");
}

async function removeRule(id: string) {
  const { error } = await api.deleteRule(id);
  if (error) report(false, "kh.allergens.profile.failed");
  else rules.value = rules.value.filter(rule => rule.id !== id);
}
</script>
