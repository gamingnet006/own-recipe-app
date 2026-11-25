// KH: the side-menu entries a person hid (D58) and their simple view switch (D79) as one shared state, loaded once per
// user like the add-on switches. The menus read khSidebar.hidden and .simple; nothing hidden and simple off until the
// answer has arrived. The language and the colour the person chose (null: none yet) travel with them.
import type { Composer } from "vue-i18n";
import { KhNavigationApi } from "../lib/api/navigation";
import { asKhAccent, type KhAccent } from "../lib/accent-colours";
import { asKhLocale, type KhLocale } from "../lib/locale";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

export const khSidebar = reactive({ hidden: [] as string[], simple: false, locale: null as KhLocale | null, accent: null as KhAccent | null, userId: null as string | null });

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
  khSidebar.simple = false;
  khSidebar.locale = null;
  khSidebar.accent = null;
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
    khSidebar.simple = data.simple;
    khSidebar.locale = asKhLocale(data.locale);
    khSidebar.accent = asKhAccent(data.accent);
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

/** Switches the simple view on or off: shown at once, stored with the current list; a failure is reported and the
 * switch goes back. */
export function saveKhSimple(simple: boolean): Promise<void> {
  const previous = khSidebar.simple;
  khSidebar.simple = simple;
  saves = saves.then(async () => {
    const { data } = await new KhNavigationApi(useRequests()).put(khSidebar.hidden, simple);
    if (!data) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      khSidebar.simple = previous;
    }
  });
  return saves;
}

/** Keeps the language the person chose on their account (shown at once, stored with the current list); a failure is
 * reported and the stored choice stays as it was. */
export function saveKhLocale(locale: KhLocale): Promise<void> {
  const previous = khSidebar.locale;
  khSidebar.locale = locale;
  saves = saves.then(async () => {
    const { data } = await new KhNavigationApi(useRequests()).put(khSidebar.hidden, undefined, locale);
    if (!data) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      khSidebar.locale = previous;
    }
  });
  return saves;
}

/** Keeps the person's own colour on their account (null: follow the installation's); shown at once, a failure is
 * reported and the old colour comes back. */
export function saveKhAccent(accent: KhAccent | null): Promise<void> {
  const previous = khSidebar.accent;
  khSidebar.accent = accent;
  saves = saves.then(async () => {
    const { data } = await new KhNavigationApi(useRequests()).put(khSidebar.hidden, undefined, undefined, accent ?? "installation");
    if (!data) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      khSidebar.accent = previous;
    }
  });
  return saves;
}
