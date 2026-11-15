// KH: the household's add-on switches (D46) as one shared state. Components read khAddons.enabled; it holds the
// defaults until the answer of the server arrives, and stays on them if it never does (retried after 60 seconds).
import type { Composer } from "vue-i18n";
import { DEFAULT_ADDONS, type KhAddonFlags, type KhAddonName, type KhAddonsAnswer } from "../lib/addons";
import { KhAddonsApi } from "../lib/api/addons";
import { clearOfflineCaches } from "../lib/offline";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

export const khAddons = reactive({
  flags: { ...DEFAULT_ADDONS } as KhAddonFlags,
  enabled: { ...DEFAULT_ADDONS } as KhAddonFlags,
  unavailable: [] as KhAddonName[],
  userId: null as string | null,
});

// When the last load failed, and for whom: every navigation runs the route guard, and a down server should not be
// asked on each of them.
let failedLoad: { userId: string; at: number } | null = null;
const RETRY_AFTER_FAILURE_MS = 60_000;

/** The switches in force, for templates: khOn.shopping. */
export function useKhOn() {
  return computed(() => khAddons.enabled);
}

/** Takes over an answer of the server (also the one of a save). Without offline recipes the saved ones go. */
export function setKhAddons(answer: KhAddonsAnswer): void {
  khAddons.flags = answer.flags;
  khAddons.enabled = answer.enabled;
  khAddons.unavailable = answer.unavailable;
  // ponytail: the service worker keeps saving while the page is open; the next start clears again
  if (!answer.enabled.offline) void clearOfflineCaches();
}

/** Back to the defaults, for another user. */
export function resetKhAddons(): void {
  setKhAddons({ flags: { ...DEFAULT_ADDONS }, enabled: { ...DEFAULT_ADDONS }, unavailable: [] });
  khAddons.userId = null;
  failedLoad = null;
}

/** Loads the household's switches once per user; the next user of the same browser gets his own. Outside a component
 * (a route guard) pass the app's i18n, because the request helper would otherwise call useI18n(). */
export async function loadKhAddonsFor(userId: string, i18n?: Composer): Promise<void> {
  if (khAddons.userId === userId) return;
  if (failedLoad?.userId === userId && Date.now() - failedLoad.at < RETRY_AFTER_FAILURE_MS) return;
  if (khAddons.userId) resetKhAddons(); // a failed load for this user must not leave the last household's switches
  const { data } = await new KhAddonsApi(useRequests(i18n)).get();
  if (data) {
    setKhAddons(data);
    khAddons.userId = userId;
  }
  else {
    failedLoad = { userId, at: Date.now() };
    console.error("Kochheft: add-ons not loaded, the defaults stay");
  }
}

/** Loads the switches as soon as a user is there (and again for another one); call it from a layout. */
export function useKhAddonsLoader(): void {
  const auth = useMealieAuth();
  watch(() => auth.user.value?.id, (id) => {
    if (id) void loadKhAddonsFor(id);
  }, { immediate: true });
}

/** Stores new switches (admins only) and takes the answer over; reports a failure and keeps the old state. */
export async function saveKhAddons(flags: KhAddonFlags): Promise<boolean> {
  const { data } = await new KhAddonsApi(useRequests()).put(flags);
  if (data) setKhAddons(data);
  else alert.error(useGlobalI18n().t("events.something-went-wrong"));
  return !!data;
}
