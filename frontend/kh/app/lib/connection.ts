// KH: the quiet reachability check of the app: does the server answer? One cheap request every few seconds while the
// page is visible; the state only changes on a real difference, so nothing flickers.

/** How often the server is asked (20 to 30 seconds is quiet enough for a battery and fast enough for a banner). */
export const CHECK_INTERVAL_MS = 25_000;
/** Failed checks in a row before the banner shows: one lost answer on weak Wi-Fi must not make it flicker. The browser's
 * own "offline" event is trusted at once. */
export const FAILED_CHECKS_BEFORE_OFFLINE = 2;
const PING_TIMEOUT_MS = 8000;
const PING_PATH = "/api/app/about"; // Mealie's cheapest public answer

/** Whether the server answers well at BASE (the sub path of the app, "" at the root); never throws. */
export async function pingServer(base: string, fetcher: typeof fetch = fetch): Promise<boolean> {
  try {
    const response = await fetcher(`${base}${PING_PATH}`, { cache: "no-store", signal: AbortSignal.timeout(PING_TIMEOUT_MS) });
    return response.ok;
  }
  catch {
    return false;
  }
}

export interface MonitorDeps {
  ping: () => Promise<boolean>;
  visible: () => boolean;
  /** Called only when the state really changes. */
  onChange: (reachable: boolean) => void;
  /** Called when the server answers again after it did not: send what waits, refresh the data. */
  onBack: () => void;
}

/** The state machine behind the banner: reachable until a check or the browser says otherwise. */
export function createMonitor(deps: MonitorDeps, initial = true) {
  let reachable = initial; // the shared state at start: a monitor started while it says "offline" must be able to end it
  let running = false;
  let failedInARow = initial ? 0 : FAILED_CHECKS_BEFORE_OFFLINE;
  let timer: ReturnType<typeof setInterval> | undefined;

  function set(next: boolean) {
    if (next === reachable) return;
    reachable = next;
    deps.onChange(next);
    if (next) deps.onBack();
  }

  /** Asks the server now (one check at a time). */
  async function check() {
    if (running) return;
    running = true;
    try {
      failedInARow = (await deps.ping()) ? 0 : failedInARow + 1;
      if (failedInARow === 0) set(true);
      else if (failedInARow >= FAILED_CHECKS_BEFORE_OFFLINE) set(false);
    }
    finally {
      running = false;
    }
  }

  return {
    check,
    /** The browser's own "offline" event: no need to ask. */
    markOffline: () => {
      failedInARow = FAILED_CHECKS_BEFORE_OFFLINE;
      set(false);
    },
    reachable: () => reachable,
    /** Checks once at once, then every interval; starting again replaces the timer. */
    start() {
      clearInterval(timer);
      if (deps.visible()) void check();
      timer = setInterval(() => {
        if (deps.visible()) void check();
      }, CHECK_INTERVAL_MS);
    },
    stop() {
      clearInterval(timer);
    },
  };
}

const WRITE_METHODS = ["post", "put", "patch", "delete"];
// The shopping list queues its own writes while offline; sign-in and sign-out must still work on the device
const SELF_HANDLING = /\/api\/(?:households\/shopping|kh\/shopping|auth)\//;

/** Whether a request (METHOD, URL) can only work with the server and so is refused with a clear note while offline. */
export function needsServer(method: string | undefined, url: string | undefined): boolean {
  return WRITE_METHODS.includes(method?.toLowerCase() ?? "get") && !SELF_HANDLING.test(url ?? "");
}
