// KH: tests for the reachability check (D63 follow-up): the interval, visible-only checks, the offline/back-online
// transitions, and the ping itself.
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { CHECK_INTERVAL_MS, FAILED_CHECKS_BEFORE_OFFLINE, createMonitor, needsServer, pingServer } from "../lib/connection";

function setup(answers: boolean[], visible = true, initial = true) {
  const queue = [...answers];
  const state = { visible };
  const deps = {
    ping: vi.fn(async () => queue.shift() ?? true),
    visible: () => state.visible,
    onChange: vi.fn(),
    onBack: vi.fn(),
  };
  return { deps, state, monitor: createMonitor(deps, initial) };
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("createMonitor", () => {
  test("checks every 20 to 30 seconds, one constant", async () => {
    expect(CHECK_INTERVAL_MS).toBeGreaterThanOrEqual(20_000);
    expect(CHECK_INTERVAL_MS).toBeLessThanOrEqual(30_000);
    const { deps, monitor } = setup([true, true]);
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 2);
    expect(deps.ping).toHaveBeenCalledTimes(3); // once at the start, then every interval
    monitor.stop();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 2);
    expect(deps.ping).toHaveBeenCalledTimes(3);
  });

  test("does not ask while the page is hidden", async () => {
    const { deps, monitor } = setup([], false);
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 3);
    expect(deps.ping).not.toHaveBeenCalled();
  });

  test("a monitor started while the shared state says offline recovers: the answer comes, banner and refresh follow", async () => {
    const { deps, monitor } = setup([true], true, false);
    expect(monitor.reachable()).toBe(false);
    monitor.start();
    await vi.advanceTimersByTimeAsync(0);
    expect(deps.onChange).toHaveBeenCalledWith(true);
    expect(deps.onBack).toHaveBeenCalledTimes(1);
  });

  test("a monitor that started offline stays offline on a failed check", async () => {
    const { deps, monitor } = setup([false], true, false);
    monitor.start();
    await vi.advanceTimersByTimeAsync(0);
    expect(deps.onChange).not.toHaveBeenCalled();
    expect(monitor.reachable()).toBe(false);
  });

  test("starting twice keeps one timer", async () => {
    const { deps, monitor } = setup([]);
    monitor.start();
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS);
    expect(deps.ping).toHaveBeenCalledTimes(2); // one start-up check (the second start finds it running), one interval check
  });

  test("one failed check on weak Wi-Fi is not enough; the banner needs two in a row", async () => {
    expect(FAILED_CHECKS_BEFORE_OFFLINE).toBe(2);
    const { deps, monitor } = setup([true, false, true, false, true]);
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 4);
    expect(deps.onChange).not.toHaveBeenCalled();
    expect(deps.onBack).not.toHaveBeenCalled();
  });

  test("no answer twice: reports offline once; the answer is back: reports it once and asks for the refresh", async () => {
    const { deps, monitor } = setup([true, false, false, false, true, true]);
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 5);
    expect(deps.onChange.mock.calls).toEqual([[false], [true]]);
    expect(deps.onBack).toHaveBeenCalledTimes(1);
    expect(monitor.reachable()).toBe(true);
  });

  test("a quiet start without trouble reports nothing", async () => {
    const { deps, monitor } = setup([true, true, true]);
    monitor.start();
    await vi.advanceTimersByTimeAsync(CHECK_INTERVAL_MS * 2);
    expect(deps.onChange).not.toHaveBeenCalled();
    expect(deps.onBack).not.toHaveBeenCalled();
  });

  test("the browser's offline event counts at once, its online event asks the server right away", async () => {
    const { deps, monitor } = setup([true]);
    monitor.markOffline();
    expect(deps.onChange).toHaveBeenCalledWith(false);
    await monitor.check();
    expect(deps.onChange).toHaveBeenLastCalledWith(true);
    expect(deps.onBack).toHaveBeenCalledTimes(1);
  });

  test("a check that is still running is not started twice", async () => {
    let finish: (value: boolean) => void = () => {};
    const deps = {
      ping: vi.fn(() => new Promise<boolean>((resolve) => { finish = resolve; })),
      visible: () => true,
      onChange: vi.fn(),
      onBack: vi.fn(),
    };
    const monitor = createMonitor(deps);
    const first = monitor.check();
    void monitor.check();
    finish(true);
    await first;
    expect(deps.ping).toHaveBeenCalledTimes(1);
  });
});

describe("needsServer", () => {
  test("writes need the server, reads do not", () => {
    expect(needsServer("post", "/api/recipes")).toBe(true);
    expect(needsServer("PUT", "/api/recipes/x")).toBe(true);
    expect(needsServer("patch", "/api/recipes/x")).toBe(true);
    expect(needsServer("delete", "/api/recipes/x")).toBe(true);
    expect(needsServer("get", "/api/recipes")).toBe(false);
    expect(needsServer(undefined, "/api/recipes")).toBe(false);
  });

  test("the shopping queue and the sign-in/out calls handle themselves", () => {
    expect(needsServer("put", "/api/households/shopping/items/1")).toBe(false);
    expect(needsServer("post", "/api/kh/shopping/anything")).toBe(false);
    expect(needsServer("post", "/api/auth/logout")).toBe(false);
  });
});

describe("pingServer", () => {
  test("true when the server answers well, false on an error status, a refusal or no network", async () => {
    expect(await pingServer("", vi.fn().mockResolvedValue({ ok: true }))).toBe(true);
    expect(await pingServer("", vi.fn().mockResolvedValue({ ok: false }))).toBe(false);
    expect(await pingServer("", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")))).toBe(false);
  });

  test("asks the cheap about address fresh, with a time limit", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true });
    await pingServer("/sub", fetcher);
    expect(fetcher).toHaveBeenCalledWith("/sub/api/app/about", expect.objectContaining({ cache: "no-store", signal: expect.anything() }));
  });
});
