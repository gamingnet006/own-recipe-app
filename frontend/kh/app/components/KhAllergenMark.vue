<!-- KH: the small warning sign on a recipe card (D44, A2) when the recipe probably contains something somebody in the
household does not tolerate. The warnings come from one shared request (use-kh-allergens). -->
<template>
  <v-icon
    v-if="warnings[slug]?.length"
    size="small"
    color="warning"
    :title="$t('kh.allergens.warning-icon')"
    :aria-label="$t('kh.allergens.warning-icon')"
  >
    {{ $globals.icons.alert }}
  </v-icon>
</template>

<script setup lang="ts">
import { useKhAllergenWarnings } from "../composables/use-kh-allergens";

defineProps<{ slug: string }>();

const { warnings } = useKhAllergenWarnings();
</script>
