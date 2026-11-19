<!-- KH: the first-sign-in tour (D59): a few short cards, shown through KhCards. Finishing or skipping closes it and
emits "done"; the "phone" card's button also opens the setup page (D68). -->
<template>
  <KhCards v-model="open" :cards="cards" :finish-label="$t('kh.tour.start')" @done="emit('done')" @action="goSetup" />
</template>

<script setup lang="ts">
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { SETUP_PATH } from "~~/kh/app/lib/device-setup";
import { tourSteps } from "~~/kh/app/lib/tour";

const open = defineModel<boolean>({ required: true });
const emit = defineEmits<{ done: [] }>();

const i18n = useI18n();
const { $globals } = useNuxtApp();
const icons = $globals.icons as Record<string, string>;

const cards = computed(() => tourSteps(khAddons.enabled).map(step => ({
  icon: icons[step.icon] ?? "",
  title: i18n.t(`kh.tour.steps.${step.key}.title`),
  text: i18n.t(`kh.tour.steps.${step.key}.text`),
  action: step.action,
  actionLabel: step.action ? i18n.t("kh.setup.start") : undefined,
})));

/** The button of the "phone" card: the tour is finished, on to the setup page. */
function goSetup() {
  void navigateTo(SETUP_PATH);
}
</script>
