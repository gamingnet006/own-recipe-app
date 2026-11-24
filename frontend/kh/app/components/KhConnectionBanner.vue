<!-- KH: the strip at the top of every page while the server is not reachable; it takes its own room, so it never covers
the page, and it is quiet (no dialog, no sound). -->
<template>
  <v-alert
    v-if="!online"
    type="warning"
    variant="tonal"
    density="compact"
    rounded="0"
    class="kh-connection-banner d-print-none"
    role="status"
  >
    {{ $t("kh.connection.banner") }}
  </v-alert>
</template>

<script setup lang="ts">
import { useKhOnline } from "../composables/use-kh-connection";

const online = useKhOnline();
</script>
