<!-- KH: "Mitteilungen" (D75): which push messages a person gets. A big switch turns them on for this device (the
permission question must come from a tap, iOS insists), then six switches, the evening time, a test button and the
person's devices. On iPhone and iPad it only works for the app on the home screen, which the page says. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.notifications.title") }}
      </template>
    </BasePageTitle>

    <v-card class="mb-4">
      <v-card-text>
        <v-switch
          :model-value="thisDevice !== null"
          color="primary"
          hide-details
          :disabled="blocker === 'unsupported' || blocker === 'install-first' || busy"
          :label="$t('kh.notifications.this-device')"
          @update:model-value="toggleDevice(!!$event)"
        />
        <v-alert v-if="blocker === 'install-first'" type="info" variant="tonal" class="mt-3">
          {{ $t("kh.notifications.install-first") }}
          <v-btn :to="SETUP_PATH" variant="text" color="primary" class="mt-1">
            {{ $t("kh.setup.title") }}
          </v-btn>
        </v-alert>
        <v-alert v-else-if="blocker === 'unsupported'" type="warning" variant="tonal" class="mt-3">
          {{ $t("kh.notifications.unsupported") }}
        </v-alert>
        <v-alert v-else-if="blocker === 'denied'" type="warning" variant="tonal" class="mt-3">
          {{ $t("kh.notifications.denied") }}
        </v-alert>
        <v-alert v-if="problem" type="error" variant="tonal" class="mt-3">
          {{ problem }}
        </v-alert>
      </v-card-text>
    </v-card>

    <v-card v-if="settings" class="mb-4">
      <v-card-text>
        <div v-for="event in EVENTS" :key="event" class="mb-1">
          <v-switch
            :model-value="settings[event]"
            color="primary"
            hide-details
            :label="$t(`kh.notifications.events.${event}.title`)"
            @update:model-value="change({ [event]: !!$event })"
          />
          <p class="text-body-2 text-medium-emphasis ml-14 mb-2">
            {{ $t(`kh.notifications.events.${event}.text`) }}
          </p>
          <v-text-field
            v-if="event === 'evening' && settings.evening"
            :model-value="settings.eveningTime"
            type="time"
            :label="$t('kh.notifications.evening-time')"
            class="ml-14 mb-2"
            style="max-width: 200px"
            @update:model-value="setTime($event)"
          />
        </div>
      </v-card-text>
      <v-card-actions class="px-4 pb-4">
        <v-btn
          variant="tonal"
          size="large"
          :disabled="devices.length === 0"
          :loading="testing"
          @click="sendTest"
        >
          {{ $t("kh.notifications.test") }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-card v-if="devices.length > 0" class="mb-4">
      <v-card-title>{{ $t("kh.notifications.devices") }}</v-card-title>
      <v-list>
        <v-list-item
          v-for="device in devices"
          :key="device.id"
          :title="device.userAgent + (device.endpoint === thisDevice ? ` (${$t('kh.setup.this-device')})` : '')"
        >
          <template #append>
            <v-btn variant="text" color="error" @click="removeDevice(device.endpoint)">
              {{ $t("kh.notifications.remove") }}
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";
import { SETUP_PATH, isInstalled } from "~~/kh/app/lib/device-setup";
import { KhNotificationsApi, type KhPushDevice } from "~~/kh/app/lib/api/notifications";
import { EVENTS, keyToBytes, pushBlocker, type KhNotificationSettings } from "~~/kh/app/lib/notifications";

definePageMeta({
  middleware: ["auth"],
});

const i18n = useI18n();
useSeoMeta({ title: i18n.t("kh.notifications.title") });
const api = new KhNotificationsApi(useRequests());

const SW_WAIT_MS = 5000; // without a service worker (development) there is nothing to wait for forever

const settings = ref<KhNotificationSettings | null>(null);
const devices = ref<KhPushDevice[]>([]);
const thisDevice = ref<string | null>(null); // endpoint of this browser's subscription, if it has one
const blocker = ref(computeBlocker());
const busy = ref(false);
const testing = ref(false);
const problem = ref("");

/** What keeps this device from push messages, from the browser's own facts. */
function computeBlocker() {
  return pushBlocker({
    userAgent: navigator.userAgent,
    touchPoints: navigator.maxTouchPoints,
    installed: isInstalled(matchMedia("(display-mode: standalone)").matches, (navigator as Navigator & { standalone?: boolean }).standalone),
    apis: "serviceWorker" in navigator && "PushManager" in window && "Notification" in window,
    permission: "Notification" in window ? Notification.permission : "default",
  });
}

/** This browser's push registration, or null when there is no service worker (yet). */
async function registration(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) return null;
  const timeout = new Promise<null>(resolve => setTimeout(resolve, SW_WAIT_MS, null));
  return await Promise.race([navigator.serviceWorker.ready, timeout]);
}

async function load() {
  const [mine, list, current] = await Promise.all([api.settings(), api.devices(), registration()]);
  settings.value = mine.data ?? null;
  devices.value = list.data ?? [];
  const subscription = blocker.value === "unsupported" ? null : await current?.pushManager.getSubscription();
  thisDevice.value = subscription?.endpoint ?? null;
}
onMounted(load);

/** Turns notifications on or off for this device. The permission question is asked right here, in the tap. */
async function toggleDevice(on: boolean) {
  problem.value = "";
  busy.value = true;
  try {
    const current = await registration();
    if (!current) throw new Error(i18n.t("kh.notifications.no-worker"));
    if (on) await subscribeHere(current);
    else await unsubscribeHere(current);
    await load();
  }
  catch (error) {
    problem.value = (error as Error).message || i18n.t("events.something-went-wrong");
  }
  finally {
    blocker.value = computeBlocker();
    busy.value = false;
  }
}

async function subscribeHere(current: ServiceWorkerRegistration) {
  if (await Notification.requestPermission() !== "granted") return;
  const { data } = await api.key();
  if (!data) throw new Error(i18n.t("events.something-went-wrong"));
  const subscription = await current.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyToBytes(data.key) });
  const { error } = await api.subscribe(subscription.toJSON());
  if (error) throw new Error(i18n.t("events.something-went-wrong"));
}

async function unsubscribeHere(current: ServiceWorkerRegistration) {
  const subscription = await current.pushManager.getSubscription();
  if (!subscription) return;
  await api.unsubscribe(subscription.endpoint);
  await subscription.unsubscribe();
}

/** Saves the changed switches at once. */
async function change(changes: Partial<KhNotificationSettings>) {
  if (!settings.value) return;
  const next = { ...settings.value, ...changes };
  const { data } = await api.putSettings(next);
  if (data) settings.value = data;
  else alert.error(i18n.t("events.something-went-wrong"));
}

/** The time field gives "" while it is being edited; only a full HH:MM is saved. */
function setTime(value: string) {
  if (/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) void change({ eveningTime: value });
}

async function sendTest() {
  testing.value = true;
  const { data } = await api.test();
  testing.value = false;
  if (data?.sent) alert.success(i18n.t("kh.notifications.test-sent"));
  else alert.error(i18n.t("kh.notifications.test-failed"));
}

async function removeDevice(endpoint: string) {
  if (endpoint === thisDevice.value) {
    await toggleDevice(false);
    return;
  }
  await api.unsubscribe(endpoint);
  await load();
}
</script>
