<!-- KH: the setup's colour choice (wave 2), right under the language: the installation's colour, saved at once and
shown at once. Without a choice the installation stays Salbei. -->
<template>
  <v-card-actions class="justify-center flex-column pb-8">
    <p class="text-subtitle-1 mb-4">
      {{ $t("kh.accent.setup") }}
    </p>
    <KhAccentChoice centered :model-value="khInstallationAccent ?? 'salbei'" @update:model-value="choose" />
    <p class="text-body-2 text-medium-emphasis mt-3 text-center">
      {{ $t("kh.accent.setup-hint") }}
    </p>
  </v-card-actions>
</template>

<script setup lang="ts">
import { KhOnboardingApi } from "../lib/api/onboarding";
import { khInstallationAccent } from "../composables/use-kh-accent";
import type { KhAccent } from "../lib/accent-colours";
import { useRequests } from "~/composables/api/api-client";

const api = new KhOnboardingApi(useRequests());

async function choose(accent: KhAccent | null) {
  if (!accent) return;
  const previous = khInstallationAccent.value;
  khInstallationAccent.value = accent;
  const { data } = await api.putAccent(accent);
  if (!data) khInstallationAccent.value = previous;
}
</script>
