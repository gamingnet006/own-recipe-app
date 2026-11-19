// KH: the side-menu entries a person hid (D58) as one shared state, loaded once per user like the add-on switches.
// The side menu and the More page read khSidebar.hidden; it is empty (all shown) until the answer has arrived.
import type { Composer } from "vue-i18n";
import { KhNavigationApi } from "../lib/api/navigation";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

export const khSidebar = reactive({ hidden: [] as string[], userId: null as string | null });

// When the last load failed, and for whom: every navigation runs the route guard, and a down server should not be
// asked on each of them.
let failedLoad: { userId: string; at: number } | null = null;
const RETRY_AFTER_FAILURE_MS = 60_000;

// Saves run one after the other, so two quick changes reach the server in the order they were made
let saves: Promise<void> = Promise.resolve();
let newest = 0; // the number of the latest save, to tell whether a finished one is still the one shown

/** Back to nothing hidden, for a signed-out browser or another user. */
export function resetKhSidebar(): void {
  khSidebar.hidden = [];
  khSidebar.userId = null;
  failedLoad = null;
}

/** Loads the person's hidden entries once per user; the next user of the same browser gets their own. A failed load
 * leaves everything shown. Outside a component (a route guard) pass the app's i18n, because the request helper would
 * otherwise call useI18n(). */
export async function loadKhSidebarFor(userId: string, i18n?: Composer): Promise<void> {
  if (khSidebar.userId === userId) return;
  if (failedLoad?.userId === userId && Date.now() - failedLoad.at < RETRY_AFTER_FAILURE_MS) return;
  resetKhSidebar();
  const { data } = await new KhNavigationApi(useRequests(i18n)).get();
  if (data) {
    khSidebar.hidden = data.hidden;
    khSidebar.userId = userId;
  }
  else {
    failedLoad = { userId, at: Date.now() };
    console.error("Kochheft: side menu settings not loaded, everything stays shown");
  }
}

/** Takes the new list over at once, so a second change made before the answer builds on it, and stores it; the
 * server's answer replaces it (unless a newer change is already shown). A failure is reported and brings the old
 * list back. */
export function saveKhSidebar(hidden: string[]): Promise<void> {
  const previous = khSidebar.hidden;
  khSidebar.hidden = hidden;
  const mine = ++newest;
  saves = saves.then(async () => {
    const { data } = await new KhNavigationApi(useRequests()).put(hidden);
    const current = mine === newest;
    if (data && current) khSidebar.hidden = data.hidden;
    else if (!data) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      if (current) khSidebar.hidden = previous;
    }
  });
  return saves;
}
