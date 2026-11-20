<!-- KH: a read-only labelled box with a copy button (D86): the address and the key on the setup page share this look. -->
<template>
  <v-text-field :model-value="value" readonly density="compact" hide-details :label="label">
    <template #append-inner>
      <v-btn icon variant="text" :aria-label="$t('kh.setup.copy')" @click="copyText(value)">
        <v-icon :icon="$globals.icons.contentCopy" />
      </v-btn>
    </template>
  </v-text-field>
</template>

<script setup lang="ts">
import { useCopy } from "~/composables/use-copy";

defineProps<{ label: string; value: string }>();
const { $globals } = useNuxtApp();
const { copyText } = useCopy(); // shows Mealie's "copied" toast (or the error when the browser refuses)
</script>
