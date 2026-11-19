<!-- KH: "Neu in Kochheft" (D69): the cards of the versions NEWS lists, shown through KhCards with the version as the
header. Finishing or skipping emits "done"; a card with a button (setup) also opens that page. -->
<template>
  <KhCards
    v-model="open"
    :cards="cards"
    :heading="heading"
    :finish-label="$t('kh.news.done')"
    @done="emit('done')"
    @action="goSetup"
  />
</template>

<script setup lang="ts">
import { SETUP_PATH } from "~~/kh/app/lib/device-setup";
import { WIZARD_PATH } from "~~/kh/app/lib/setup-wizard";
import { newsTextKey, type KhNewsVersion } from "~~/kh/app/lib/whats-new";

const props = defineProps<{ news: KhNewsVersion[] }>();
const open = defineModel<boolean>({ required: true });
const emit = defineEmits<{ done: [] }>();

const i18n = useI18n();
const { $globals } = useNuxtApp();
const icons = $globals.icons as Record<string, string>;

const cards = computed(() => props.news.flatMap(entry => entry.cards.map(card => ({
  icon: icons[card.icon] ?? "",
  title: i18n.t(`${newsTextKey(entry.version, card)}.title`),
  text: i18n.t(`${newsTextKey(entry.version, card)}.text`),
  action: card.action,
  actionLabel: card.action ? i18n.t(card.action === "wizard" ? "kh.wizard.open" : "kh.setup.start") : undefined,
}))));
// Several versions in one run (an update skipped one): the header names the newest, which is the one that counts
const heading = computed(() => i18n.t("kh.news.title", { version: props.news[0]?.version ?? "" }));

/** The button of a card: the news are finished, on to the device setup page or (admin card, D83) the first-time setup. */
function goSetup(action: string) {
  void navigateTo(action === "wizard" ? WIZARD_PATH : SETUP_PATH);
}
</script>
