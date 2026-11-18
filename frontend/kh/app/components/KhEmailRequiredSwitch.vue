<!-- KH: admin switch "e-mail address required" (D53): people who sign in must give a confirmed address. Off and
     disabled while mail sending is not set up. -->
<template>
  <v-switch
    v-model="required"
    class="px-4"
    color="primary"
    density="compact"
    :disabled="!$khFeatures.emailReady || loading"
    :label="$t('kh.onboarding.admin.email-required')"
    :hint="$khFeatures.emailReady ? $t('kh.onboarding.admin.email-required-hint') : $t('kh.onboarding.admin.needs-mail')"
    persistent-hint
    @update:model-value="save"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { failureText } from "../lib/onboarding";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

const i18n = useI18n();
const api = new KhOnboardingApi(useRequests());
const required = ref(false);
const loading = ref(true);

onMounted(async () => {
  const { data } = await api.getSettings();
  required.value = data?.emailRequired ?? false;
  loading.value = false;
});

/** Saves the switch; on a refusal (e.g. mail not set up) shows the server's message and turns it back. */
async function save(value: boolean | null) {
  const { data, error } = await api.putSettings(!!value);
  if (error) alert.error(failureText(error, i18n.t("events.something-went-wrong")));
  required.value = data?.emailRequired ?? !value;
}
</script>
