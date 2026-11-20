<!-- KH: "Kochheft einrichten" (D68): per device a few cards with short steps to get the app onto the home screen or
the Dock, the shopping list as an own icon, a key for the shortcuts, and the shortcuts themselves. Each card can be
ticked off; the ticks stay on this device. The key is shown once and never stored. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.setup.title") }}
      </template>
    </BasePageTitle>

    <p class="text-body-1 mb-3">
      {{ $t("kh.setup.intro") }}
    </p>
    <v-select
      v-model="device"
      :items="deviceItems"
      :label="$t('kh.setup.device')"
      :hint="$t('kh.setup.device-hint')"
      persistent-hint
      class="mb-4"
    />

    <v-card v-for="section in plans" :key="section.id" class="mb-4" :class="{ 'kh-done': isDone(section.id) }">
      <v-card-title class="text-wrap d-flex align-center">
        <v-icon :icon="icon(SECTION_ICON[section.id])" class="mr-2" color="primary" />
        {{ $t(`kh.setup.${section.id}.${family}.title`) }}
      </v-card-title>
      <v-card-text>
        <p v-if="section.id === 'home' && installed" class="text-body-2 mb-2">
          {{ $t("kh.setup.home.installed") }}
        </p>
        <p v-if="section.id === 'import' && shortcutUrl(section.id)" class="text-body-1">
          {{ $t("kh.setup.import.with-link") }}
        </p>
        <p v-else-if="section.id === 'siri' && shortcutUrl(section.id)" class="text-body-1">
          {{ $t("kh.setup.siri.with-link") }}
        </p>
        <ol v-else class="pl-5">
          <li v-for="n in section.steps" :key="n" class="mb-1 text-body-1">
            {{ $t(`kh.setup.${section.id}.${family}.s${n}`) }}
          </li>
        </ol>

        <v-btn
          v-if="section.id === 'list' && family !== 'android'"
          href="/einkauf"
          target="_blank"
          rel="noopener"
          color="primary"
          size="large"
          :prepend-icon="$globals.icons.openInNew"
          class="mt-3"
        >
          {{ $t("kh.setup.list.open") }}
        </v-btn>

        <!-- D81: QR code for the fridge and NFC sticker -->
        <template v-if="section.id === 'kitchen'">
          <div class="text-center mt-3">
            <img :src="qrSrc" :alt="$t('kh.setup.kitchen.qr-alt')" width="200" height="200">
            <p class="text-body-2 text-break">
              {{ listUrl }}
            </p>
          </div>
          <v-btn
            color="primary"
            size="large"
            :prepend-icon="$globals.icons.printer"
            class="mt-2 mr-2"
            @click="printQr"
          >
            {{ $t("kh.setup.kitchen.print") }}
          </v-btn>
          <v-btn
            v-if="nfcWritable"
            color="primary"
            variant="tonal"
            size="large"
            class="mt-2"
            @click="writeNfc"
          >
            {{ $t("kh.setup.kitchen.nfc") }}
          </v-btn>
          <p class="text-body-2 text-medium-emphasis mt-3">
            {{ $t("kh.setup.kitchen.sticker-note") }}
          </p>
        </template>

        <template v-if="section.id === 'key'">
          <v-btn color="primary" size="large" :loading="making" class="mt-3" @click="makeKey">
            {{ $t("kh.setup.key.make") }}
          </v-btn>
          <v-alert v-if="madeKey" type="warning" variant="tonal" class="mt-3">
            <p class="font-weight-bold text-break">
              {{ madeKey }}
            </p>
            <v-btn variant="tonal" size="large" :prepend-icon="$globals.icons.contentCopy" class="my-2" @click="copyText(madeKey)">
              {{ $t("kh.setup.key.copy") }}
            </v-btn>
            <p class="text-body-2">
              {{ $t("kh.setup.key.once") }}
            </p>
          </v-alert>
        </template>

        <template v-if="(section.id === 'import' || section.id === 'siri') && shortcutUrl(section.id)">
          <v-btn
            :href="shortcutUrl(section.id)!"
            target="_blank"
            rel="noopener"
            color="primary"
            size="large"
            class="mt-3"
          >
            {{ $t("kh.setup.add-shortcut") }}
          </v-btn>
          <p class="text-body-2 mt-3 mb-1">
            {{ $t("kh.setup.asks-for") }}
          </p>
          <v-text-field :model-value="shortcutAddress" readonly density="compact" hide-details :label="$t('kh.setup.address')">
            <template #append-inner>
              <v-btn icon variant="text" :aria-label="$t('kh.setup.key.copy')" @click="copyText(shortcutAddress)">
                <v-icon :icon="$globals.icons.contentCopy" />
              </v-btn>
            </template>
          </v-text-field>
        </template>

        <v-btn v-if="section.id === 'timer'" :to="settingsPath" variant="tonal" size="large" class="mt-3">
          {{ $t("kh.setup.timer.open") }}
        </v-btn>
      </v-card-text>
      <v-card-actions class="px-4 pb-3">
        <v-checkbox
          :model-value="isDone(section.id)"
          color="primary"
          hide-details
          density="comfortable"
          :label="$t('kh.setup.done')"
          @update:model-value="setDone(section.id, !!$event)"
        />
      </v-card-actions>
    </v-card>

    <!-- D81: what the browser prints while the QR is printed: only the code with its caption (see the style below) -->
    <Teleport to="body">
      <div class="kh-qr-sheet" aria-hidden="true">
        <img :src="qrSrc" alt="" width="600" height="600">
        <p class="kh-qr-caption">
          {{ $t("kh.setup.kitchen.caption") }}
        </p>
        <p>{{ listUrl }}</p>
      </div>
    </Teleport>

    <p v-if="family === 'android' && khOn.shopping" class="text-body-2 text-medium-emphasis">
      {{ $t("kh.setup.siri.android-note") }}
    </p>
  </v-container>
</template>

<script setup lang="ts">
import { renderSVG } from "uqr";
import { khAddons, useKhOn } from "~~/kh/app/composables/use-kh-addons";
import {
  DEVICES,
  detectDevice,
  familyOf,
  isInstalled,
  canWriteNfc,
  keyName,
  parseDone,
  printQrSheet,
  setupSections,
  shoppingUrl,
  withDone,
  type KhDevice,
  type KhSetupSection,
} from "~~/kh/app/lib/device-setup";
import { welcomeAddress } from "~~/kh/app/lib/setup-wizard";
import { useCopy } from "~/composables/use-copy";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth"],
});

const i18n = useI18n();
const { $globals, $khFeatures } = useNuxtApp();
const auth = useMealieAuth();
const api = useUserApi();
const { copyText } = useCopy();
const khOn = useKhOn();
useSeoMeta({ title: i18n.t("kh.setup.title") });

const SECTION_ICON: Record<KhSetupSection, string> = {
  home: "cellphone",
  list: "cartCheck",
  kitchen: "qrCode",
  key: "keyVariant",
  import: "import",
  siri: "microphone",
  timer: "calendar",
};

/** One of Mealie's icons by its name. */
const icon = (name: string) => ($globals.icons as Record<string, string>)[name] ?? "";

const detected = detectDevice(navigator.userAgent, navigator.maxTouchPoints);
const device = ref<KhDevice>(detected);
const family = computed(() => familyOf(device.value));
const deviceItems = computed(() =>
  DEVICES.map(d => ({ value: d, title: i18n.t(`kh.setup.devices.${d}`) + (d === detected ? ` (${i18n.t("kh.setup.this-device")})` : "") })));
const plans = computed(() => setupSections(device.value, khAddons.enabled));

const installed = isInstalled(
  matchMedia("(display-mode: standalone)").matches,
  (navigator as Navigator & { standalone?: boolean }).standalone,
);
const origin = location.origin;
const shortcutAddress = welcomeAddress($khFeatures.baseUrl, origin); // KH: the configured address, which the shortcuts ask for (D85)
const settingsPath = computed(() => `/g/${auth.user.value?.groupSlug ?? ""}/einstellungen`); // KH: the timer switch sits there (D76)

/** The ready-made shortcut's iCloud link for the import or Siri section, null while none is set. */
function shortcutUrl(id: KhSetupSection): string | null {
  return id === "import" ? $khFeatures.importShortcutUrl : id === "siri" ? $khFeatures.siriShortcutUrl : null;
}

// Ticks stay on this device, per person; storage that is blocked or broken just means nothing is ticked
const doneKey = `kh-setup-done:${auth.user.value?.id ?? ""}`;
function readDone(): KhSetupSection[] {
  try {
    return parseDone(localStorage.getItem(doneKey));
  }
  catch {
    return [];
  }
}
const done = ref(readDone());
const isDone = (id: KhSetupSection) => done.value.includes(id) || (id === "home" && installed);

/** Ticks a card off or back on and remembers it on this device. */
function setDone(id: KhSetupSection, ticked: boolean) {
  done.value = withDone(done.value, id, ticked);
  try {
    localStorage.setItem(doneKey, JSON.stringify(done.value));
  }
  catch {
    // not stored: the tick still shows until the page closes
  }
}

// The QR code and the NFC sticker hold the address of the shopping list (D81)
const listUrl = shoppingUrl(origin);
const qrSrc = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(renderSVG(listUrl))}`;
const nfcWritable = canWriteNfc(window);

/** Opens the browser's print dialog; the style below makes it print only the code sheet. */
const printQr = () => printQrSheet(document.documentElement, window);

/** Writes the address to an NFC sticker held to the phone (Android Chrome); a refusal is told, not hidden. */
async function writeNfc() {
  try {
    const reader = new (window as unknown as { NDEFReader: new () => { write: (message: object) => Promise<void> } }).NDEFReader();
    await reader.write({ records: [{ recordType: "url", data: listUrl }] });
    alert.success(i18n.t("kh.setup.kitchen.nfc-done"));
  }
  catch {
    alert.error(i18n.t("kh.setup.kitchen.nfc-failed"));
  }
}

// The key lives only in this variable: shown once, never stored
const madeKey = ref("");
const making = ref(false);

/** Makes a Mealie API token for this person and device and shows it. */
async function makeKey() {
  making.value = true;
  const { data } = await api.users.createAPIToken({ name: keyName(device.value, new Date()) });
  making.value = false;
  if (data) madeKey.value = data.token;
  else alert.error(i18n.t("events.something-went-wrong"));
}
onBeforeUnmount(() => {
  madeKey.value = "";
});
</script>

<style scoped>
.kh-done {
  opacity: 0.75;
}
</style>

<style>
/* D81: the code sheet exists only for printing the QR: html.kh-print-qr is set while it prints (printQrSheet), so
   recipe and cookbook prints are not touched; everything else is taken out of the page then, no blank extra pages */
.kh-qr-sheet {
  display: none;
}
@media print {
  html.kh-print-qr body > *:not(.kh-qr-sheet) {
    display: none !important;
  }
  html.kh-print-qr .kh-qr-sheet {
    display: block;
    text-align: center;
    padding-top: 2cm;
  }
  html.kh-print-qr .kh-qr-sheet img {
    width: 14cm;
    height: 14cm;
  }
  html.kh-print-qr .kh-qr-caption {
    font-size: 28pt;
    font-weight: 600;
  }
}
</style>
