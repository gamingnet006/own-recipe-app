<!-- KH: "Which store?" (D60): the store presets as chips by kind and a free name; emits the choice, the page makes the list. -->
<template>
  <v-dialog :model-value="modelValue" max-width="480" @update:model-value="emit('update:modelValue', $event)">
    <v-card class="pa-4">
      <h3 class="text-h6 font-weight-bold mb-2">
        {{ $t("kh.shopping.which-store") }}
      </h3>
      <div v-for="kind in STORE_KINDS" :key="kind" class="mb-3">
        <div class="text-caption text-medium-emphasis mb-1">
          {{ $t(`kh.shopping.kinds.${kind}`) }}
        </div>
        <div class="d-flex flex-wrap ga-2">
          <v-chip
            v-for="preset in STORE_PRESETS.filter(entry => entry.kind === kind)"
            :key="preset.name"
            @click="pick(preset)"
          >
            {{ preset.name }}
          </v-chip>
        </div>
      </div>
      <v-text-field
        v-model="other"
        :label="$t('kh.shopping.other-store')"
        variant="solo-filled"
        flat
        hide-details
        :append-inner-icon="$globals.icons.check"
        @click:append-inner="pickOther"
        @keydown.enter="pickOther"
      />
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { STORE_KINDS, STORE_PRESETS, type StorePreset } from "../lib/shopping-stores";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [open: boolean]; "pick": [store: StorePreset] }>();

const other = ref("");

function pick(store: StorePreset) {
  emit("pick", store);
  other.value = "";
}

/** A free name gets the supermarket order. */
function pickOther() {
  const name = other.value.trim();
  if (name) pick({ name, kind: "supermarket" });
}
</script>
