<!-- KH: "More > System check" (P8.3), admins only: one traffic light per row, nothing is changed here, and below it the
first-start list with links. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.system") }}
      </template>
      {{ $t("kh.system.description") }}
    </BasePageTitle>

    <v-alert v-if="failed" type="error" variant="tonal">
      {{ $t("kh.system.failed") }}
    </v-alert>
    <v-list v-else-if="rows.length" rounded="lg" class="py-0 mb-6">
      <v-list-item
        v-for="row in rows"
        :key="row.key"
        :prepend-icon="icon(LIGHTS[row.state].icon)"
        :base-color="LIGHTS[row.state].color"
        :title="rowText($t, row)"
      />
    </v-list>
    <v-progress-linear v-else indeterminate />

    <h2 class="text-h6 mb-2">
      {{ $t("kh.system.start.title") }}
    </h2>
    <!-- D46, G1: the question that only sets the two big switches -->
    <KhAddonPresets class="mb-4" />
    <v-list rounded="lg" class="py-0">
      <v-list-item
        v-for="step in steps"
        :key="step.key"
        :to="step.external ? undefined : step.to"
        :href="step.external ? step.to : undefined"
        :target="step.external ? '_blank' : undefined"
        :rel="step.external ? 'noopener' : undefined"
        :title="$t(`kh.system.start.${step.key}`)"
        :append-icon="$globals.icons.chevronRight"
      />
    </v-list>
  </v-container>
</template>

<script setup lang="ts">
import { KhSystemApi, type KhCheck } from "~~/kh/app/lib/api/system";
import { firstStartSteps, LIGHTS, rowText } from "~~/kh/app/lib/system";
import { useRequests } from "~/composables/api/api-client";

definePageMeta({
  middleware: ["auth", "admin-only"],
});

const i18n = useI18n();
const { $globals, $khFeatures } = useNuxtApp();
useSeoMeta({ title: i18n.t("kh.nav.system") });

const rows = ref<KhCheck[]>([]);
const failed = ref(false);
const steps = firstStartSteps($khFeatures.sourceUrl);

/** One of Mealie's icons by its name; empty when unknown. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}

onMounted(async () => {
  const { data } = await new KhSystemApi(useRequests()).checks();
  rows.value = data ?? [];
  failed.value = !data;
});
</script>

<style scoped>
/* Long check texts (the default account, the AI provider) wrap on a phone instead of ending in "…" */
.v-list-item :deep(.v-list-item-title) {
  white-space: normal;
}
</style>
