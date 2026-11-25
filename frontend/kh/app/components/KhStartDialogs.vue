<!-- KH: the one dialog the start page may open for a signed-in person (D59 tour, the question about intolerances, D69 news, D85 new address, D68 setup question); see
startDialog() for the order. The setup question is asked once per person and device. -->
<template>
  <div>
    <KhTour v-model="showTour" @done="onTourDone" />
    <KhIntolerancesDialog v-if="showIntolerances" v-model="showIntolerances" />
    <KhNews v-model="showNews" :news="news" @done="onNewsDone" />
    <KhCards
      v-model="showAddress"
      :cards="addressCards"
      :finish-label="$t('kh.address.done')"
      @done="onAddressDone"
      @action="() => navigateTo(SETUP_PATH)"
    />
    <v-dialog v-model="showDevice" max-width="480" persistent>
      <v-card>
        <v-card-title class="text-wrap pt-4">
          {{ $t("kh.setup.prompt.title") }}
        </v-card-title>
        <v-card-text class="text-body-1">
          {{ $t(computer ? "kh.setup.prompt.text-computer" : "kh.setup.prompt.text-phone") }}
        </v-card-text>
        <v-card-actions class="flex-wrap px-4 pb-4">
          <v-btn variant="text" size="large" @click="answerDevice('never')">
            {{ $t("kh.setup.prompt.never") }}
          </v-btn>
          <v-btn variant="text" size="large" @click="answerDevice('later')">
            {{ $t("kh.setup.prompt.later") }}
          </v-btn>
          <v-spacer />
          <v-btn color="primary" variant="flat" size="large" @click="answerDevice('yes')">
            {{ $t("kh.setup.prompt.yes") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { addressCardDue, addressSeenKey } from "~~/kh/app/lib/address-change";
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { khOnboarding, useKhOnboarding } from "~~/kh/app/composables/use-kh-onboarding";
import { detectDevice, familyOf, parseAnswer, SETUP_PATH, shouldAskDevice } from "~~/kh/app/lib/device-setup";
import { type KhStartDialog, startDialog } from "~~/kh/app/lib/start-dialog";
import { unseenNews, WHATS_NEW } from "~~/kh/app/lib/whats-new";

const i18n = useI18n();
const userId = useMealieAuth().user.value?.id ?? "";
const answerKey = `kh-device-setup:${userId}`;

const device = detectDevice(navigator.userAgent, navigator.maxTouchPoints);
const computer = ["mac", "computer"].includes(familyOf(device));

/** The stored answer of this device; a blocked or broken storage counts as no answer. */
function storedAnswer() {
  try {
    return parseAnswer(localStorage.getItem(answerKey));
  }
  catch {
    return null;
  }
}

// The news are read once when the start page opens; a finished dialog is skipped by startDialog() and the next follows
const news = unseenNews(khOnboarding.status?.newsSeen ?? null, WHATS_NEW, khAddons.enabled, !!useMealieAuth().user.value?.admin);
const { $khFeatures, $globals } = useNuxtApp();
const seenKey = addressSeenKey(userId);

/** What this device has stored as the seen address change; blocked storage counts as not seen. */
function storedSeen() {
  try {
    return localStorage.getItem(seenKey);
  }
  catch {
    return null;
  }
}

const finished: KhStartDialog[] = [];
/** The dialog due now, given what was answered on this page already. */
const dueDialog = () => startDialog({
  status: khOnboarding.status,
  signedIn: !!userId,
  allergensOn: khAddons.enabled.allergens,
  hasNews: news.length > 0,
  addressChanged: addressCardDue($khFeatures.addressChangedAt, storedSeen()),
  askDevice: shouldAskDevice(storedAnswer(), device, navigator.userAgent, Date.now()),
  done: finished,
});
const current = ref(dueDialog());

/** v-model of one dialog: open while it is the due one; closing it moves on to the next due dialog at once. */
function shown(name: KhStartDialog) {
  return computed({
    get: () => current.value === name,
    set: (open: boolean) => {
      if (open || current.value !== name) return;
      finished.push(name);
      current.value = dueDialog();
    },
  });
}
const showTour = shown("tour");
const showIntolerances = shown("intolerances");
const showNews = shown("news");
const showAddress = shown("address");
const showDevice = shown("device");
const addressCards = [{
  icon: ($globals.icons as Record<string, string>).cellphone ?? "",
  title: i18n.t("kh.address.title"),
  text: i18n.t("kh.address.text", { address: $khFeatures.baseUrl ?? location.origin }),
  action: "setup",
  actionLabel: i18n.t("kh.setup.start"),
}];

const onTourDone = () => useKhOnboarding().finishTour(i18n.t("events.something-went-wrong"));
const onNewsDone = () => useKhOnboarding().finishNews(WHATS_NEW[0]!.version, i18n.t("events.something-went-wrong"));

/** Remembers on this device that the card was seen, so it comes once. */
function onAddressDone() {
  try {
    localStorage.setItem(seenKey, $khFeatures.addressChangedAt ?? "");
  }
  catch {
    // storage blocked: the card may come back, which is harmless
  }
}

/** Stores the answer on this device ("later" asks again after a week, "never" and "yes" not at all) and opens the
 * setup page on yes. */
function answerDevice(answer: "later" | "never" | "yes") {
  try {
    localStorage.setItem(answerKey, JSON.stringify({ answer, at: Date.now() }));
  }
  catch {
    // storage blocked: the question may come back, which is harmless
  }
  showDevice.value = false;
  if (answer === "yes") void navigateTo(SETUP_PATH);
}
</script>
