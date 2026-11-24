<!-- KH: two buttons that move a photo one place earlier or later (arrows, so it works by touch and keyboard too). -->
<template>
  <span class="d-inline-flex">
    <v-btn
      icon
      size="small"
      variant="tonal"
      :disabled="index === 0"
      :aria-label="$t('kh.drafts.photo-earlier', { n: index + 1 })"
      @click="move(-1)"
    >
      <v-icon :icon="vertical ? $globals.icons.arrowUp : $globals.icons.chevronLeft" />
    </v-btn>
    <v-btn
      icon
      size="small"
      variant="tonal"
      :disabled="index === count - 1"
      :aria-label="$t('kh.drafts.photo-later', { n: index + 1 })"
      @click="move(1)"
    >
      <v-icon :icon="vertical ? $globals.icons.arrowDown : $globals.icons.chevronRight" />
    </v-btn>
  </span>
</template>

<script setup lang="ts">
import { movedOrder } from "../lib/photo-order";

const props = defineProps<{ index: number; count: number; vertical?: boolean }>();
const emit = defineEmits<{ order: [order: number[]] }>();

function move(by: -1 | 1) {
  const order = movedOrder(props.count, props.index, by);
  if (order) emit("order", order);
}
</script>
