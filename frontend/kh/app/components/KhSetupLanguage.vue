<!-- KH: the first thing of the setup wizard (wave 2): Deutsch or English. Shown in English until chosen; the choice is
saved as the installation's language and on the admin's own account. Opened again, it shows the current choice. -->
<template>
  <v-card-actions class="justify-center flex-column py-8">
    <p class="text-subtitle-1 mb-4">
      {{ $t("kh.wizard.language") }}
    </p>
    <KhLanguageButtons :model-value="i18n.locale.value" @choose="choose" />
  </v-card-actions>
</template>

<script setup lang="ts">
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { chooseKhLocale } from "../composables/use-kh-locale";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { FALLBACK_LOCALE, type KhLocale } from "../lib/locale";
import { useRequests } from "~/composables/api/api-client";

/** True once the installation has a language (chosen now or earlier); the wizard waits for it on a first run. */
const chosen = defineModel<boolean>("chosen", { default: false });
const props = defineProps<{ rerun: boolean }>();

const i18n = useGlobalI18n();
const api = new KhOnboardingApi(useRequests());

// A fresh install has no language yet: English until the admin chooses (a device in German does not decide here)
onMounted(async () => {
  const { data } = await api.getSettings();
  chosen.value = !!data?.locale;
  if (!data?.locale && !props.rerun) await i18n.setLocale(FALLBACK_LOCALE);
});

async function choose(locale: KhLocale) {
  await chooseKhLocale(locale, true, i18n);
  const { data } = await api.putLocale(locale);
  chosen.value = !!data?.locale;
}
</script>
