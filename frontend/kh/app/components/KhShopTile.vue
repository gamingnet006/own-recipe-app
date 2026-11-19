<!-- KH: one tile of the shopping page (D60): emoji or first letter, name, small detail line and an urgency badge.
Tap emits "press"; a long press (450 ms) or the right mouse button emits "hold". A house badge (top left) marks a
food that is always in the house (D65). -->
<template>
  <button
    type="button"
    class="kh-tile"
    :class="`kh-tile--${variant}`"
    @pointerdown="start"
    @pointerup="stop"
    @pointerleave="stop"
    @pointercancel="stop"
    @click="onClick"
    @contextmenu.prevent="onContextMenu"
  >
    <span class="kh-tile__emoji" aria-hidden="true">{{ emoji || name.charAt(0).toUpperCase() }}</span>
    <span class="kh-tile__name">{{ name }}</span>
    <span v-if="detail" class="kh-tile__detail">{{ detail }}</span>
    <v-icon v-if="badge" :icon="badge" size="14" class="kh-tile__badge" />
    <v-icon v-if="onHand" :icon="mdiHome" size="14" class="kh-tile__house" />
  </button>
</template>

<script setup lang="ts">
import { mdiHome } from "@mdi/js";

const HOLD_MS = 450;

defineProps<{
  name: string;
  emoji?: string;
  detail?: string;
  /** An mdi icon for the urgency, top right */
  badge?: string;
  /** Always in the house: a house badge, top left */
  onHand?: boolean;
  /** list: still to buy; done: bought; catalog: not on the list; new: write down a new name */
  variant: "list" | "done" | "catalog" | "new";
}>();
const emit = defineEmits<{ press: []; hold: [] }>();

let timer: ReturnType<typeof setTimeout> | undefined;
let held = false;

function start() {
  held = false;
  timer = setTimeout(() => {
    held = true;
    emit("hold");
  }, HOLD_MS);
}

function stop() {
  clearTimeout(timer);
}

/** A tap that ends a long press must not also count as a tap. */
function onClick() {
  if (!held) emit("press");
}

/** The right mouse button; on a phone the long press fires a context menu too, which the hold already handled. */
function onContextMenu() {
  if (!held) emit("hold");
  held = true;
}
</script>

<style scoped>
.kh-tile {
  aspect-ratio: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px;
  border-radius: 14px;
  text-align: center;
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-on-surface), 0.08);
  transition: transform 0.12s;
  -webkit-touch-callout: none;
  user-select: none;
}

.kh-tile:active {
  transform: scale(0.95);
}

.kh-tile:focus-visible {
  outline: 3px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.kh-tile--list {
  background: rgb(var(--v-theme-error));
  color: rgb(var(--v-theme-on-error));
}

.kh-tile--done {
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.kh-tile--new {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.3);
  background: transparent;
}

.kh-tile__emoji {
  font-size: 34px;
  line-height: 1;
}

.kh-tile__name {
  font-weight: 700;
  font-size: 13px;
  line-height: 1.15;
  overflow-wrap: anywhere;
}

.kh-tile__detail {
  font-size: 11px;
  opacity: 0.85;
  line-height: 1.15;
}

.kh-tile__badge {
  position: absolute;
  top: 5px;
  right: 6px;
}

.kh-tile__house {
  position: absolute;
  top: 5px;
  left: 6px;
  opacity: 0.6;
}
@media (prefers-reduced-motion: reduce) {
  .kh-tile {
    transition: none;
  }
}
</style>
