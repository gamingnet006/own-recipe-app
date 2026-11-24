// KH: whether the server is reachable, as one shared state: the browser's online flag plus the quiet check of
// lib/connection.ts. Pages read useKhOnline(); code that must run once the server is back registers onKhReconnect().
// One monitor serves the whole app; the layout only runs its timer, the browser's events are watched from a plugin, so
// the state also follows the connection on pages that have no layout (admin, sign-in).
import { useOnline } from "@vueuse/core";
import { createMonitor, pingServer } from "../lib/connection";

const reachable = ref(true);
const reconnectCallbacks = new Set<() => void>();
let monitor: ReturnType<typeof createMonitor> | undefined;

function getMonitor() {
  if (!monitor) {
    const base = String(useNuxtApp().$config.public.SUB_PATH ?? "").replace(/\/+$/, "");
    monitor = createMonitor({
      ping: () => pingServer(base),
      visible: () => document.visibilityState === "visible",
      onChange: (next) => { reachable.value = next; },
      onBack: () => reconnectCallbacks.forEach(callback => callback()),
    }, reachable.value);
  }
  return monitor;
}

/** True while the browser has a network and the server answers; for banners, disabled buttons and the offline paths. */
export function useKhOnline() {
  const browser = useOnline();
  return computed(() => browser.value && reachable.value);
}

/** The same answer for code outside a component (a request hook). */
export const isKhOnline = (): boolean => navigator.onLine && reachable.value;

/** Runs CALLBACK whenever the server answers again after it did not; ends with the calling component or scope. */
export function onKhReconnect(callback: () => void): void {
  reconnectCallbacks.add(callback);
  if (getCurrentScope()) onScopeDispose(() => reconnectCallbacks.delete(callback));
}

/** Runs the check every 25 s while the layout is mounted (and once at its start). */
export function useKhConnectionMonitor(): void {
  onMounted(() => getMonitor().start());
  onBeforeUnmount(() => getMonitor().stop());
}

/** Follows the browser's own events for the whole life of the app (call once from a plugin): "offline" counts at once,
 * "online" and a page that becomes visible ask the server right away. */
export function watchBrowserConnection(): void {
  const check = () => void getMonitor().check();
  window.addEventListener("online", check);
  window.addEventListener("offline", () => getMonitor().markOffline());
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") check();
  });
}
