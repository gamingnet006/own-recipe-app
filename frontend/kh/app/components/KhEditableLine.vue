<!-- KH: one line of the draft preview that can be changed right there (D55): the title, an ingredient or a step. Shows
its content (slot) with a pencil; tapping the line or the pencil turns it into a field. Enter (not in a text area) or
leaving the field saves, Escape cancels; a failed save keeps the field open. The parent says which line is open, so only one is edited at a time. -->
<template>
  <div v-if="!active" class="kh-line" :class="{ 'kh-line--editable': editable }" @click="onTap">
    <div class="kh-line__body">
      <slot />
    </div>
    <v-btn
      v-if="editable"
      class="kh-line__pencil"
      icon
      variant="text"
      size="small"
      :aria-label="$t('kh.drafts.edit.pencil')"
      @click.stop="emit('start')"
    >
      <v-icon size="small">
        {{ $globals.icons.edit }}
      </v-icon>
    </v-btn>
  </div>
  <component
    :is="multiline ? VTextarea : VTextField"
    v-else
    v-model="value"
    :label="label"
    autofocus
    auto-grow
    rows="2"
    variant="outlined"
    density="comfortable"
    hide-details
    class="my-1"
    @keydown.enter="onEnter"
    @keydown.esc.stop="cancel"
    @blur="finish"
  />
</template>

<script setup lang="ts">
import { VTextarea, VTextField } from "vuetify/components";

const props = defineProps<{
  editable: boolean;
  active: boolean;
  text: string; // what the field starts with
  save: (text: string) => Promise<boolean>; // sends a changed text; false keeps the field open with the typed text
  label: string;
  multiline?: boolean;
}>();
const emit = defineEmits<{ start: []; cancel: [] }>();

const value = ref(props.text);
let closed = false; // Enter and Escape unmount the field, which blurs it once more

watch(() => props.active, (active) => {
  if (!active) return;
  value.value = props.text;
  closed = false;
});

/** A tap on the line itself opens it; a tap on a button inside it (a step's amount) does not. */
function onTap(event: MouseEvent) {
  if (props.editable && !(event.target as HTMLElement).closest("button")) emit("start");
}

function onEnter(event: KeyboardEvent) {
  if (!props.multiline) {
    event.preventDefault();
    finish();
  }
}

/** Saves a changed text, else just closes; after a failed save Enter and leaving the field work again. */
async function finish() {
  if (closed) return;
  closed = true;
  if (value.value.trim() === props.text.trim()) emit("cancel");
  else if (!(await props.save(value.value))) closed = false;
}

function cancel() {
  closed = true;
  emit("cancel");
}
</script>

<style scoped>
.kh-line {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}
.kh-line__body {
  flex: 1;
  min-width: 0;
}
.kh-line--editable {
  cursor: pointer;
  min-height: 44px; /* a touch target */
  align-items: center;
  border-radius: 4px;
}
.kh-line--editable:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}
.kh-line__pencil {
  opacity: 0.55;
}
.kh-line:hover .kh-line__pencil,
.kh-line__pencil:focus-visible {
  opacity: 1;
}
</style>
