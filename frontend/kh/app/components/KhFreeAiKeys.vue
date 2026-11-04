<template>
  <!-- KH: where free AI keys come from, with the day the list was checked (D39) -->
  <v-card variant="outlined" class="mt-6">
    <v-card-title class="d-flex flex-wrap align-center text-title-medium">
      <v-icon start>
        {{ $globals.icons.information }}
      </v-icon>
      {{ $t("kh.ai.free-keys.title") }}
      <span class="text-body-small ms-2">({{ $t("kh.ai.free-keys.date", { date }) }})</span>
    </v-card-title>
    <v-card-text>
      <p class="mb-3">
        {{ $t("kh.ai.free-keys.hint") }}
      </p>
      <div v-for="place in FREE_AI_KEYS" :key="place.name" class="mb-4">
        <a :href="place.keyUrl" target="_blank" rel="noopener noreferrer" class="text-title-small">
          {{ place.name }}: {{ $t("kh.ai.free-keys.get-key") }}
        </a>
        <div class="text-body-small">
          {{ note(place) }}
        </div>
        <div class="d-flex align-center">
          <span class="text-body-small me-1">{{ $t("kh.ai.free-keys.address") }}:</span>
          <code class="text-body-small text-break">{{ place.baseUrl }}</code>
          <AppButtonCopy :copy-text="place.baseUrl" />
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { FREE_AI_KEYS, FREE_AI_KEYS_DATE, type FreeAiKey } from "../lib/free-ai-keys";

const i18n = useI18n();

/** The checking day in the reader's way, e.g. 4.11.2026. */
const date = computed(() => new Date(`${FREE_AI_KEYS_DATE}T12:00:00`).toLocaleDateString(i18n.locale.value));

/** The note in German for German readers, else in English. */
function note(place: FreeAiKey): string {
  return i18n.locale.value.startsWith("de") ? place.note.de : place.note.en;
}
</script>
