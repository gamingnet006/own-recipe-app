<!-- KH: the two language buttons, Deutsch and English, for the language dialog and the first setup (wave 2). -->
<template>
  <div class="d-flex flex-wrap ga-3 justify-center">
    <v-btn
      v-for="language in KH_LOCALES"
      :key="language.value"
      size="x-large"
      rounded
      :variant="language.value === modelValue ? 'flat' : 'outlined'"
      color="primary"
      class="px-10"
      :lang="language.value"
      @click="emit('choose', language.value)"
    >
      {{ language.name }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { KH_LOCALES, type KhLocale } from "../lib/locale";

defineProps<{ modelValue: string | null }>();
const emit = defineEmits<{ choose: [locale: KhLocale] }>();
</script>
