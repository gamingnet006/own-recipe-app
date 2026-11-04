<template>
  <!-- KH: the AI priority list in Mealie's AI settings (D39): the group's providers top to bottom, each with its state,
       ▲▼ to move it and Mealie's edit and delete buttons -->
  <div>
    <p class="text-body-medium mb-3">
      {{ $t("kh.ai.order-hint") }}
    </p>
    <v-card
      v-for="(provider, index) in providers"
      :key="provider.providerId"
      variant="tonal"
      class="mb-3"
    >
      <div class="d-flex align-center pa-1">
        <div class="d-flex flex-column">
          <v-btn
            icon
            variant="text"
            :aria-label="$t('kh.ai.move-up')"
            :disabled="index === 0"
            @click="$emit('move', index, -1)"
          >
            <v-icon>{{ $globals.icons.arrowUp }}</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            :aria-label="$t('kh.ai.move-down')"
            :disabled="index === providers.length - 1"
            @click="$emit('move', index, 1)"
          >
            <v-icon>{{ $globals.icons.arrowDown }}</v-icon>
          </v-btn>
        </div>
        <div class="flex-grow-1 ms-2 py-2">
          <div class="text-title-medium">
            {{ index + 1 }}. {{ provider.name }}
          </div>
          <div class="text-body-small">
            {{ provider.model }}
          </div>
          <div class="d-flex flex-wrap ga-1 mt-2">
            <v-chip size="small" :color="statusColor(provider)">
              {{ statusLabel(provider, (key, values) => i18n.t(key, values ?? {}), time) }}
            </v-chip>
            <v-chip v-if="provider.supportsImages" size="small">
              {{ $t("kh.ai.reads-images") }}
            </v-chip>
            <v-chip v-else-if="provider.supportsImages === false" size="small">
              {{ $t("kh.ai.no-images") }}
            </v-chip>
          </div>
        </div>
        <BaseButtonGroup
          :buttons="[
            { icon: $globals.icons.edit, text: $t('general.edit'), event: 'edit' },
            { icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete' },
          ]"
          @edit="$emit('edit', provider.providerId)"
          @delete="$emit('delete', provider.providerId)"
        />
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import type { KhProviderState } from "../lib/api/ai";
import { clockTime, shownStatus, statusLabel } from "../composables/use-kh-ai";

defineProps<{ providers: KhProviderState[] }>();
defineEmits<{ move: [index: number, delta: -1 | 1]; edit: [id: string]; delete: [id: string] }>();

const i18n = useI18n();

/** A pause's end as the reader's clock shows it. */
function time(date: Date): string {
  return clockTime(date, i18n.locale.value);
}

/** Green when ready, amber while paused, red while waiting for a fix. */
function statusColor(provider: KhProviderState): string {
  const status = shownStatus(provider, new Date());
  if (status === "ready") return "success";
  return status === "key" || status === "model" ? "error" : "warning";
}
</script>
