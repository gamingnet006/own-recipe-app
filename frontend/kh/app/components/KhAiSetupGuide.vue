<template>
  <!-- Step-by-step Gemini setup for people who have never filled in an AI provider; open while none exists. The
       preset buttons open Mealie's provider window already filled in, so only the key is left to paste. -->
  <v-expansion-panels :model-value="startOpen ? 0 : undefined" class="mb-4">
    <v-expansion-panel :title="$t('kh.ai.guide.title')">
      <v-expansion-panel-text>
        <ol class="pl-4">
          <li class="mb-3">
            {{ $t("kh.ai.guide.key") }}
            <a :href="gemini.keyUrl" target="_blank" rel="noopener">{{ gemini.keyUrl }}</a>
          </li>
          <li class="mb-3">
            {{ $t("kh.ai.guide.preset") }}
            <v-btn color="primary" class="mt-2" block @click="$emit('preset', GEMINI_PRESETS[0]!)">
              {{ $t("kh.ai.guide.preset-main") }}
            </v-btn>
          </li>
          <li class="mb-3">
            {{ $t("kh.ai.guide.test") }}
          </li>
          <li>
            {{ $t("kh.ai.guide.reserve") }}
            <v-btn variant="tonal" class="mt-2" block @click="$emit('preset', GEMINI_PRESETS[1]!)">
              {{ $t("kh.ai.guide.preset-reserve") }}
            </v-btn>
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
import { FREE_AI_KEYS, GEMINI_PRESETS } from "../lib/free-ai-keys";

defineProps<{ startOpen: boolean }>();
defineEmits<{ preset: [preset: (typeof GEMINI_PRESETS)[number]] }>();

const gemini = FREE_AI_KEYS.find(key => key.baseUrl.includes("generativelanguage"))!;
</script>
