<!-- KH: the shopping page's list name: a tap turns it into a text field; Enter or "Done" saves, Escape cancels. -->
<template>
  <v-text-field
    v-if="editing"
    v-model="draft"
    autofocus
    hide-details
    density="compact"
    class="flex-grow-1"
    :label="$t('kh.shopping.rename-label')"
    @keydown.enter.prevent="save"
    @keydown.esc="editing = false"
  >
    <template #append-inner>
      <v-btn variant="text" size="small" :disabled="!cleanListName(draft)" @click="save">
        {{ $t("kh.shopping.rename-done") }}
      </v-btn>
    </template>
  </v-text-field>
  <h1
    v-else
    class="text-h6 font-weight-bold flex-grow-1 text-truncate"
    :style="{ cursor: canRename ? 'text' : undefined }"
    @click="begin"
  >
    {{ name }}
  </h1>
</template>

<script setup lang="ts">
import { cleanListName } from "../lib/shopping-items";

const props = defineProps<{ name: string; editable: boolean; disabled: boolean }>();
const emit = defineEmits<{ save: [name: string] }>();

const editing = ref(false);
const draft = ref("");
const canRename = computed(() => props.editable && !props.disabled);

/** Opens the text field with the current name; does nothing when renaming is not possible (no list, no connection). */
function begin() {
  if (!canRename.value) return;
  draft.value = props.name;
  editing.value = true;
}

function save() {
  if (!cleanListName(draft.value)) return;
  editing.value = false;
  emit("save", draft.value);
}

defineExpose({ begin });
</script>
