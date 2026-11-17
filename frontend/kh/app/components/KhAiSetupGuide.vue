<template>
  <!-- Step-by-step Gemini setup for people who have never filled in an AI provider; open while none exists -->
  <v-expansion-panels :model-value="startOpen ? 0 : undefined" class="mb-4">
    <v-expansion-panel :title="$t('kh.ai.guide.title')">
      <v-expansion-panel-text>
        <ol class="pl-4">
          <li class="mb-3">
            {{ $t("kh.ai.guide.key") }}
            <a :href="gemini.keyUrl" target="_blank" rel="noopener">{{ gemini.keyUrl }}</a>
          </li>
          <li class="mb-3">
            {{ $t("kh.ai.guide.create") }}
          </li>
          <li class="mb-3">
            {{ $t("kh.ai.guide.fields") }}
            <div v-for="field in fields" :key="field.label" class="d-flex align-center flex-wrap ga-1 mt-1">
              <strong>{{ field.label }}:</strong>
              <code v-if="field.copy">{{ field.value }}</code>
              <span v-else>{{ field.value }}</span>
              <AppButtonCopy v-if="field.copy" :copy-text="field.value" />
            </div>
          </li>
          <li class="mb-3">
            {{ $t("kh.ai.guide.test") }}
          </li>
          <li>
            {{ $t("kh.ai.guide.reserve", { model: GEMINI_MODELS[1] }) }}
            <AppButtonCopy :copy-text="GEMINI_MODELS[1]" />
          </li>
        </ol>
        <v-alert type="info" variant="tonal" density="compact" class="mt-3">
          {{ $t("kh.ai.guide.mistakes") }}
        </v-alert>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
import { FREE_AI_KEYS, GEMINI_MODELS } from "../lib/free-ai-keys";

defineProps<{ startOpen: boolean }>();

const i18n = useI18n();
const gemini = FREE_AI_KEYS.find(key => key.baseUrl.includes("generativelanguage"))!;

// The dialog's fields in its order, with Mealie's own labels so the guide matches what the person sees
const fields = computed(() => [
  { label: i18n.t("group.ai-provider-settings.provider-name"), value: "Gemini", copy: false },
  { label: i18n.t("group.ai-provider-settings.model"), value: GEMINI_MODELS[0], copy: true },
  { label: i18n.t("group.ai-provider-settings.api-key"), value: i18n.t("kh.ai.guide.paste-key"), copy: false },
  { label: i18n.t("group.ai-provider-settings.base-url"), value: gemini.baseUrl, copy: true },
  { label: i18n.t("group.ai-provider-settings.request-timeout-seconds"), value: i18n.t("kh.ai.guide.leave"), copy: false },
]);
</script>
