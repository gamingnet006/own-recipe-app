<!-- KH: the one dialog the start page may open for a signed-in person (D59 tour, D69 news, D68 setup question); see
startDialog() for the order. The setup question is asked once per person and device. -->
<template>
  <div>
    <KhTour v-model="showTour" @done="onTourDone" />
    <KhNews v-model="showNews" :news="news" @done="onNewsDone" />
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
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { khOnboarding, useKhOnboarding } from "~~/kh/app/composables/use-kh-onboarding";
import { detectDevice, familyOf, parseAnswer, SETUP_PATH, shouldAskDevice } from "~~/kh/app/lib/device-setup";
import { startDialog } from "~~/kh/app/lib/start-dialog";
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

// Decided once when the start page opens, so a finished dialog does not make the next one pop up
const news = unseenNews(khOnboarding.status?.newsSeen ?? null, WHATS_NEW, khAddons.enabled, !!useMealieAuth().user.value?.admin);
const chosen = startDialog({
  status: khOnboarding.status,
  signedIn: !!userId,
  hasNews: news.length > 0,
  askDevice: shouldAskDevice(storedAnswer(), device, navigator.userAgent, Date.now()),
});
const showTour = ref(chosen === "tour");
const showNews = ref(chosen === "news");
const showDevice = ref(chosen === "device");

const onTourDone = () => useKhOnboarding().finishTour(i18n.t("events.something-went-wrong"));
const onNewsDone = () => useKhOnboarding().finishNews(WHATS_NEW[0]!.version, i18n.t("events.something-went-wrong"));

/** Stores the answer on this device ("later" asks again after a week, "never" and "yes" not at all) and opens the
 * setup page on yes. */
function answerDevice(answer: "later" | "never" | "yes") {
  showDevice.value = false;
  try {
    localStorage.setItem(answerKey, JSON.stringify({ answer, at: Date.now() }));
  }
  catch {
    // storage blocked: the question may come back, which is harmless
  }
  if (answer === "yes") void navigateTo(SETUP_PATH);
}
</script>
