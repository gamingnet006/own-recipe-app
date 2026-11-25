<!-- KH: the question "Verträgst du etwas nicht?", asked once per account at the start page (only with the add-on
Allergene): the same ticks as the page "Ich vertrage nicht". Saving and skipping both end the question for good. -->
<template>
  <v-dialog v-model="open" max-width="480" persistent scrollable>
    <v-card>
      <v-card-title class="text-wrap pt-4">
        {{ $t("kh.allergens.ask.title") }}
      </v-card-title>
      <v-card-text>
        <p class="mb-2">
          {{ $t("kh.allergens.ask.text") }}
        </p>
        <v-progress-linear v-if="loading" indeterminate />
        <KhAllergenChoices v-else :selected="selected" @toggle="(key, on) => selected = toggleAllergen(selected, key, on)" />
      </v-card-text>
      <v-card-actions class="px-4 pb-4">
        <v-btn variant="text" size="large" data-testid="intolerances-skip" @click="finish(false)">
          {{ $t("kh.allergens.ask.skip") }}
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          size="large"
          :disabled="loading"
          data-testid="intolerances-save"
          @click="finish(true)"
        >
          {{ $t("kh.allergens.ask.save") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { refreshKhAllergenWarnings } from "../composables/use-kh-allergens";
import { useKhOnboarding } from "../composables/use-kh-onboarding";
import { KhAllergensApi, toggleAllergen, type KhAllergenKey } from "../lib/api/allergens";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

const open = defineModel<boolean>({ default: false });
const { t } = useI18n();
const api = new KhAllergensApi(useRequests());
const selected = ref<KhAllergenKey[]>([]);
const loading = ref(true);

// A person asked for the first time may have ticked things on the profile page before: start from those
onMounted(async () => {
  selected.value = (await api.getAllergies()).data?.allergens ?? [];
  loading.value = false;
});

/** Closes the question for good; with SAVE the ticks are stored first. A failed save keeps the dialog open. */
async function finish(save: boolean) {
  if (save) {
    const { data } = await api.putAllergies(selected.value);
    if (!data) {
      alert.error(t("kh.allergens.profile.failed"));
      return;
    }
    void refreshKhAllergenWarnings();
  }
  open.value = false;
  await useKhOnboarding().finishIntolerances(t("events.something-went-wrong"));
}
</script>
