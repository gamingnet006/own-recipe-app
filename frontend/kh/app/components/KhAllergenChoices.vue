<!-- KH: the 14 allergen groups as ticks (D44): which ones a person does not tolerate. The page "Ich vertrage nicht", the
start question and the setup wizard's family step all show this list. -->
<template>
  <div>
    <v-checkbox
      v-for="key in KH_ALLERGENS"
      :key="key"
      :data-testid="`intolerance-${key}`"
      :model-value="selected.includes(key)"
      :label="$t(`kh.allergens.names.${key}`)"
      color="primary"
      density="compact"
      hide-details
      @update:model-value="emit('toggle', key, !!$event)"
    />
  </div>
</template>

<script setup lang="ts">
import { KH_ALLERGENS, type KhAllergenKey } from "../lib/api/allergens";

defineProps<{ selected: readonly KhAllergenKey[] }>();
const emit = defineEmits<{ toggle: [key: KhAllergenKey, on: boolean] }>();
</script>
