<!-- KH: the "Automatic updates" checkbox of the admin settings (P8.2). It writes data/kh/auto_update.json, which the
host's auto_update.sh reads before KH_AUTO_UPDATE; the last run's line comes from the same folder. -->
<template>
  <section class="mt-6">
    <h2 class="text-h6 mb-2">
      {{ $t("kh.system.auto-update.title") }}
    </h2>
    <v-card>
      <v-card-text>
        <v-checkbox
          :model-value="state?.enabled ?? false"
          :indeterminate="state !== null && state.enabled === null"
          :disabled="state === null || saving"
          :label="$t('kh.system.auto-update.label')"
          :hint="$t('kh.system.auto-update.hint')"
          persistent-hint
          color="primary"
          @update:model-value="save(!!$event)"
        />
        <p v-if="state" class="text-body-2 text-medium-emphasis mt-2">
          <template v-if="state.enabled === null">
            {{ $t("kh.system.auto-update.env") }}
          </template>
          {{ state.status ? $t("kh.system.auto-update.last", { status: state.status }) : $t("kh.system.auto-update.never") }}
        </p>
      </v-card-text>
    </v-card>
  </section>
</template>

<script setup lang="ts">
import { KhSystemApi, type KhAutoUpdate } from "~~/kh/app/lib/api/system";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

const i18n = useI18n();
const api = new KhSystemApi(useRequests());
const state = ref<KhAutoUpdate | null>(null);
const saving = ref(false);

/** Stores the checkbox; on a failure the old value stays and the admin is told. */
async function save(enabled: boolean) {
  saving.value = true;
  const { data } = await api.setAutoUpdate(enabled);
  if (data) state.value = data;
  else alert.error(i18n.t("kh.system.auto-update.failed"));
  saving.value = false;
}

onMounted(async () => {
  state.value = (await api.getAutoUpdate()).data;
});
</script>
