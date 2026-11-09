// KH: the household's add-on switches (D46) as one shared state. Components read khAddons.enabled; it holds the
// defaults until the answer of the server arrives, and stays on them if it never does.
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

/** Back to the defaults, e.g. for another user. */
export function resetKhAddons(): void {
  setKhAddons({ flags: { ...DEFAULT_ADDONS }, enabled: { ...DEFAULT_ADDONS }, unavailable: [] });
  khAddons.userId = null;
}

/** Loads the household's switches once per user; the next user of the same browser gets his own. */
export async function loadKhAddonsFor(userId: string): Promise<void> {
  if (khAddons.userId === userId) return;
  const { data } = await new KhAddonsApi(useRequests()).get();
  if (data) {
    setKhAddons(data);
    khAddons.userId = userId;
  }
  else {
    console.error("Küchenhelfer: add-ons not loaded, the defaults stay");
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
