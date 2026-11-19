<!-- KH: the setup wizard's "Prüfen" step (D83): the system check's rows that matter on the first day (backup, USB copy,
automatic updates, remote access, mail, AI), from the same API and shown with the same row list. Nothing is changed here. -->
<template>
  <div>
    <p class="mb-4">
      {{ $t("kh.wizard.check.intro") }}
    </p>
    <v-alert v-if="failed" type="error" variant="tonal">
      {{ $t("kh.system.failed") }}
    </v-alert>
    <KhSystemRows v-else-if="rows.length" :rows="rows" />
    <v-progress-linear v-else indeterminate />
  </div>
</template>

<script setup lang="ts">
import KhSystemRows from "./KhSystemRows.vue";
import { KhSystemApi, type KhCheck } from "../lib/api/system";
import { compactCheck } from "../lib/setup-wizard";
import { useRequests } from "~/composables/api/api-client";

const { $khFeatures } = useNuxtApp();
const rows = ref<KhCheck[]>([]);
const failed = ref(false);

onMounted(async () => {
  const { data } = await new KhSystemApi(useRequests()).checks();
  rows.value = data ? compactCheck(data, $khFeatures.emailReady) : [];
  failed.value = !data;
});
</script>
