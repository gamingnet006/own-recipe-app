<!-- KH: Back and Next of one of the wizard's own steps (D83), so each step block in Mealie's setup page stays short. -->
<template>
  <v-stepper-actions :disabled="disabled" prev-text="general.back" @click:prev="emit('prev')">
    <template #next>
      <v-btn variant="flat" color="success" :disabled="disabled" :text="$t(nextText ?? 'general.next')" @click="emit('next')" />
    </template>
  </v-stepper-actions>
</template>

<script setup lang="ts">
defineProps<{ disabled: boolean; nextText?: string }>();
const emit = defineEmits<{ prev: []; next: [] }>();
</script>
