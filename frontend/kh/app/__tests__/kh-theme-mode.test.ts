// KH: tests for the three-way look choice System / Hell / Dunkel: the stored value of vueuse stays ("auto", "light",
// "dark"), "System" follows the device live, and a broken stored value falls back to "System".
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { nextTick } from "vue";
import { parseThemeChoice, resolveTheme } from "../lib/theme";

const STORAGE_KEY = "vueuse-color-scheme";

test("only auto, light and dark are choices; anything else counts as System", () => {
  expect(["auto", "light", "dark"].map(parseThemeChoice)).toEqual(["auto", "light", "dark"]);
  expect([null, undefined, "", "blue", 3].map(parseThemeChoice)).toEqual(["auto", "auto", "auto", "auto", "auto"]);
});

test("System takes the device's look, Hell and Dunkel their own", () => {
  expect(resolveTheme("auto", true)).toBe("dark");
  expect(resolveTheme("auto", false)).toBe("light");
  expect(resolveTheme("light", true)).toBe("light");
  expect(resolveTheme("dark", false)).toBe("dark");
});

// A matchMedia whose answer the test can change, with the listeners the browser would call.
let systemDark = false;
const listeners = new Set<(event: { matches: boolean }) => void>();
const mediaQuery = {
  get matches() { return systemDark; },
  addEventListener: (_: string, fn: (event: { matches: boolean }) => void) => listeners.add(fn),
  removeEventListener: (_: string, fn: (event: { matches: boolean }) => void) => listeners.delete(fn),
};
function stubMatchMedia() {
  vi.stubGlobal("matchMedia", () => mediaQuery);
  window.matchMedia = globalThis.matchMedia;
}

async function fresh() {
  vi.resetModules();
  return (await import("../composables/use-kh-theme")).useKhTheme();
}

beforeEach(() => {
  localStorage.clear();
  systemDark = false;
  listeners.clear();
  document.documentElement.className = "";
  stubMatchMedia();
});

afterEach(() => vi.unstubAllGlobals());

test("an earlier choice carries over: the stored 'dark' is Dunkel, nothing stored is System", async () => {
  localStorage.setItem(STORAGE_KEY, "dark");
  expect((await fresh()).choice.value).toBe("dark");
  localStorage.clear();
  expect((await fresh()).choice.value).toBe("auto");
});

test("choosing stores the value under the old key and sets the page's class", async () => {
  const { choice, resolved } = await fresh();
  choice.value = "dark";
  await nextTick();
  expect(localStorage.getItem(STORAGE_KEY)).toBe("dark");
  expect(resolved.value).toBe("dark");
  expect(document.documentElement.classList.contains("dark")).toBe(true);
  choice.value = "light";
  await nextTick();
  expect(resolved.value).toBe("light");
  expect(document.documentElement.classList.contains("dark")).toBe(false);
});

test("System follows the device while the page is open", async () => {
  const { choice, resolved } = await fresh();
  expect(choice.value).toBe("auto");
  expect(resolved.value).toBe("light");
  systemDark = true;
  listeners.forEach(fn => fn({ matches: true }));
  await nextTick();
  expect(resolved.value).toBe("dark");
});
