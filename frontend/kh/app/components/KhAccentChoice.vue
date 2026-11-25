<!-- KH: the ten colour swatches as a radio group (wave 2); the chosen colour's name is shown under the row. With
"with-installation" a person may also give their own colour up ("Wie die Installation"). -->
<template>
  <div>
    <div role="radiogroup" :aria-label="$t('kh.accent.title')" :class="['d-flex', 'flex-wrap', 'ga-3', { 'justify-center': centered }]">
      <v-btn
        v-for="key in KH_ACCENT_KEYS"
        :key="key"
        icon
        size="small"
        role="radio"
        :aria-checked="modelValue === key"
        :aria-label="$t(`kh.accent.${key}`)"
        :title="$t(`kh.accent.${key}`)"
        :style="{ backgroundColor: swatch(key) }"
        @click="emit('update:modelValue', key)"
      >
        <v-icon v-if="modelValue === key" :icon="$globals.icons.check" color="white" />
      </v-btn>
    </div>
    <p :class="['text-body-2', 'mt-2', 'mb-0', { 'text-center': centered }]">
      {{ $t(`kh.accent.${modelValue ?? 'installation'}`) }}
    </p>
    <v-btn
      v-if="withInstallation && modelValue !== null"
      variant="text"
      size="small"
      class="px-0 mt-1"
      @click="emit('update:modelValue', null)"
    >
      {{ $t("kh.accent.installation") }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { useKhTheme } from "../composables/use-kh-theme";
import { KH_ACCENT_KEYS, KH_ACCENTS, type KhAccent } from "../lib/accent-colours";

defineProps<{ modelValue: KhAccent | null; withInstallation?: boolean; centered?: boolean }>();
const emit = defineEmits<{ "update:modelValue": [accent: KhAccent | null] }>();

const { resolved } = useKhTheme();

/** The swatch shows the colour as it looks in the current look. */
function swatch(key: KhAccent): string {
  return KH_ACCENTS[key][resolved.value].primary;
}
</script>
