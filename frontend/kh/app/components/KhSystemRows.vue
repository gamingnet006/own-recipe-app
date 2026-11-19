<!-- KH: the traffic lights of the system check (P8.3), one row per check; used by the system check page and by the
first-time setup's compact check (D83). -->
<template>
  <v-list rounded="lg" class="py-0">
    <v-list-item
      v-for="row in rows"
      :key="row.key"
      :prepend-icon="icon(LIGHTS[row.state].icon)"
      :base-color="LIGHTS[row.state].color"
      :title="rowText($t, row)"
    />
  </v-list>
</template>

<script setup lang="ts">
import type { KhCheck } from "../lib/api/system";
import { LIGHTS, rowText } from "../lib/system";

defineProps<{ rows: KhCheck[] }>();

const { $globals } = useNuxtApp();

/** One of Mealie's icons by its name; empty when unknown. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}
</script>

<style scoped>
/* Long check texts (the default account, the AI provider) wrap on a phone instead of ending in "…" */
.v-list-item :deep(.v-list-item-title) {
  white-space: normal;
}
</style>
