// KH: tests for the cook-mode timers (D42): end times that survive sleep, ranges, pause, several timers, storage in
// localStorage, the alarm's limit, and the link to the clock app.
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import type { KhTime } from "../lib/times";

const STORAGE_KEY = "kh-timers";
const ten: KhTime = { start: 0, end: 7, text: "10 Min.", seconds: 600, upperSeconds: null };
const range: KhTime = { start: 0, end: 10, text: "20-30 Min.", seconds: 1200, upperSeconds: 1800 };

let clock = 0;
const now = () => clock;

// The timers live in module state, so each test loads the module anew, as a page reload would.
async function fresh() {
  vi.resetModules();
  return await import("../composables/use-kh-timers");
}

beforeEach(() => {
  clock = 1_000_000;
  localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test("runs for its seconds, then rings", async () => {
  const { useKhTimers } = await fresh();
  const t = useKhTimers(now);
  const timer = t.start(ten, "Schritt 1", "kuchen");
  clock += 599_000;
  expect(t.left(timer)).toBe(1);
  expect(t.done(timer)).toBe(false);
  clock += 1_000;
  expect(t.done(timer)).toBe(true);
  expect(t.ringing.value.map(r => r.id)).toEqual([timer.id]);
});

test("a long sleep shows done at once", async () => {
  const { useKhTimers } = await fresh();
  const t = useKhTimers(now);
  const timer = t.start(ten, "Schritt 1", "kuchen");
  clock += 3_600_000;
  expect(t.done(timer)).toBe(true);
  expect(t.left(timer)).toBe(0);
});

test("a range rings at the lower end and extends by the difference", async () => {
  const { useKhTimers } = await fresh();
  const t = useKhTimers(now);
  const timer = t.start(range, "Schritt 2", "kuchen");
  clock += 1_200_000;
  expect(t.done(timer)).toBe(true);
  t.extend(timer.id);
  expect(t.done(timer)).toBe(false);
  expect(timer.extraSeconds).toBeNull();
  clock += 600_000;
  expect(t.done(timer)).toBe(true);
});

test("a paused timer keeps its time", async () => {
  const { useKhTimers } = await fresh();
  const t = useKhTimers(now);
  const timer = t.start(ten, "Schritt 1", "kuchen");
  clock += 500_000;
  t.pause(timer.id);
  clock += 1_000_000;
  expect(t.left(timer)).toBe(100);
  t.resume(timer.id);
  expect(t.left(timer)).toBe(100);
  clock += 100_000;
  expect(t.done(timer)).toBe(true);
});

test("timers run independently", async () => {
  const { useKhTimers } = await fresh();
  const t = useKhTimers(now);
  const first = t.start(ten, "Schritt 1", "kuchen");
  const second = t.start(range, "Schritt 2", "kuchen");
  t.stop(first.id);
  expect(t.timers.value.map(x => x.id)).toEqual([second.id]);
});

test("timers survive a reload; broken storage gives an empty list", async () => {
  let mod = await fresh();
  const started = mod.useKhTimers(now).start(ten, "Schritt 1", "kuchen");
  mod = await fresh();
  expect(mod.useKhTimers(now).timers.value).toEqual([started]);

  localStorage.setItem(STORAGE_KEY, "{not json");
  mod = await fresh();
  expect(mod.useKhTimers(now).timers.value).toEqual([]);
  localStorage.setItem(STORAGE_KEY, "{\"a\":1}");
  mod = await fresh();
  expect(mod.useKhTimers(now).timers.value).toEqual([]);
});

test("the link to the clock app", async () => {
  const { clockTimerUrl } = await fresh();
  expect(clockTimerUrl("KH Timer", 61)).toBe("shortcuts://run-shortcut?name=KH%20Timer&input=text&text=2");
});

test("the alarm beeps and vibrates until stopped or the limit", async () => {
  const { startAlarm, unlockAudio, ALARM_MAX_MS } = await fresh();
  const beep = vi.fn();
  class FakeAudio {
    destination = {};
    currentTime = 0;
    resume = vi.fn();
    createOscillator = () => ({ connect: vi.fn(), start: beep, stop: vi.fn(), frequency: { value: 0 } });
  }
  const vibrate = vi.fn();
  vi.stubGlobal("AudioContext", FakeAudio);
  vi.stubGlobal("navigator", { vibrate });
  vi.useFakeTimers();

  unlockAudio();
  const stop = startAlarm();
  vi.advanceTimersByTime(2500);
  expect(beep.mock.calls.length).toBeGreaterThanOrEqual(2);
  expect(vibrate).toHaveBeenCalledWith([300, 200, 300]);
  stop();
  const calls = beep.mock.calls.length;
  vi.advanceTimersByTime(5000);
  expect(beep).toHaveBeenCalledTimes(calls);

  startAlarm();
  vi.advanceTimersByTime(ALARM_MAX_MS + 1);
  const atLimit = beep.mock.calls.length;
  vi.advanceTimersByTime(5000);
  expect(beep).toHaveBeenCalledTimes(atLimit);
});

// The step display needs Mealie's i18n set-up; its times are all the handler takes from it (tested in kh-step-text).
vi.mock("../lib/step-text", async importOriginal => ({
  ...(await importOriginal<typeof import("../lib/step-text")>()),
  khStepDisplay: () => ({ html: "", times: [ten] }),
}));

test("a tap on a time starts its timer and stops there; a tap elsewhere does nothing", async () => {
  vi.stubGlobal("AudioContext", class { resume = vi.fn(); });
  const { useKhTimers } = await fresh();
  const { useKhTimeTap } = await import("../composables/use-kh-time-tap");
  const step = { id: "s", text: "Teig 10 Min. ruhen", title: "", summary: "", ingredientReferences: [] };
  const recipe = { slug: "kuchen", recipeIngredient: [], recipeInstructions: [step] } as never;
  const container = document.createElement("div");
  container.innerHTML = "<p>Teig <span class=\"kh-time\">10 Min.</span> ruhen</p>";
  const clickOn = (target: Element) => {
    const event = new MouseEvent("click", { bubbles: true });
    const stop = vi.spyOn(event, "stopPropagation");
    container.addEventListener("click", e => useKhTimeTap()(e, 0, step, recipe, 1), { once: true });
    target.dispatchEvent(event);
    return stop;
  };

  expect(clickOn(container.querySelector("p")!)).not.toHaveBeenCalled();
  expect(useKhTimers(now).timers.value).toEqual([]);
  expect(clickOn(container.querySelector("span")!)).toHaveBeenCalled();
  const [timer] = useKhTimers(now).timers.value;
  expect(timer).toMatchObject({ label: "1. Teig 10 Min. ruhen", recipeSlug: "kuchen", seconds: 600 });
});

describe("the clock shortcut setting", () => {
  const KEY = "kh-clock-timer";
  const standard = { enabled: false, name: "KH Timer" };
  const read = async () => {
    const { enabled, name } = (await fresh()).useKhClockSetting();
    return { enabled: enabled.value, name: name.value };
  };

  test("off and named KH Timer at first", async () => {
    expect(await read()).toEqual(standard);
  });
  test("stored values come back, and changes are stored", async () => {
    localStorage.setItem(KEY, JSON.stringify({ enabled: true, name: "Mein Timer" }));
    expect(await read()).toEqual({ enabled: true, name: "Mein Timer" });
    const setting = (await fresh()).useKhClockSetting();
    setting.name.value = "Uhr";
    setting.enabled.value = false;
    expect(JSON.parse(localStorage.getItem(KEY)!)).toEqual({ enabled: false, name: "Uhr" });
  });
  test("broken or foreign storage gives the standard", async () => {
    localStorage.setItem(KEY, "{not json");
    expect(await read()).toEqual(standard);
    localStorage.setItem(KEY, "[1]");
    expect(await read()).toEqual(standard);
  });
});

test("only one alarm rings, however often the alarm is requested, and it ends when the timer is stopped", async () => {
  const vibrate = vi.fn();
  vi.stubGlobal("navigator", { vibrate });
  vi.useFakeTimers();
  const { useKhAlarm, useKhTimers } = await fresh();

  // Every page and the step view ask for the alarm; the timers are never given a clock of their own here.
  useKhAlarm();
  useKhAlarm();
  const timers = useKhTimers();
  const timer = timers.start(ten, "Schritt 1", "kuchen");
  await vi.advanceTimersByTimeAsync(ten.seconds * 1000 + 1500);
  expect(vibrate).toHaveBeenCalled();

  vibrate.mockClear();
  await vi.advanceTimersByTimeAsync(3000);
  expect(vibrate).toHaveBeenCalledTimes(3); // one round per second; a second alarm would make it 6

  timers.stop(timer.id);
  await vi.advanceTimersByTimeAsync(1500); // the list notices the stop within a tick
  vibrate.mockClear();
  await vi.advanceTimersByTimeAsync(3000);
  expect(vibrate).not.toHaveBeenCalled();
});
