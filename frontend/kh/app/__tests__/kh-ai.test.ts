// KH: tests for the AI list in the settings (D39): moving a provider up or down, when the own list shows instead of
// Mealie's, the words for each state, and the free keys with their date.
import { expect, test } from "vitest";
import { moveProvider, sameProviders, statusLabel } from "../composables/use-kh-ai";
import type { KhProviderState } from "../lib/api/ai";
import { FREE_AI_KEYS, FREE_AI_KEYS_DATE } from "../lib/free-ai-keys";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

/** A tiny i18n: looks a key up in the German texts and fills in {placeholders}. */
function t(key: string, values: Record<string, string> = {}): string {
  const text = key.split(".").reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], de);
  return typeof text === "string" ? text.replace(/\{(\w+)\}/g, (_, name: string) => values[name] ?? "") : key;
}

/** Hours and minutes as in Germany in winter (UTC+1). */
const time = (d: Date) => `${d.getUTCHours() + 1}:${String(d.getUTCMinutes()).padStart(2, "0")}`;

/** Every key path in a nested texts object, sorted. */
function keys(node: object, prefix = ""): string[] {
  return Object.entries(node)
    .flatMap(([key, value]) => (typeof value === "object" ? keys(value, `${prefix}${key}.`) : [`${prefix}${key}`]))
    .sort();
}

function provider(status: string): KhProviderState {
  return { providerId: "a", name: "A", model: "m", position: 0, status, pausedUntil: "2026-11-04T08:00:00Z", supportsImages: null };
}

test("moving up and down, never past the ends", () => {
  expect(moveProvider(["a", "b", "c"], 1, -1)).toEqual(["b", "a", "c"]);
  expect(moveProvider(["a", "b", "c"], 1, 1)).toEqual(["a", "c", "b"]);
  expect(moveProvider(["a", "b", "c"], 0, -1)).toEqual(["a", "b", "c"]);
  expect(moveProvider(["a", "b", "c"], 2, 1)).toEqual(["a", "b", "c"]);
});

test("the own list shows only for the own group's providers", () => {
  expect(sameProviders(["a", "b"], ["b", "a"])).toBe(true);
  expect(sameProviders(["a"], ["c"])).toBe(false);
  expect(sameProviders(["a"], ["a", "c"])).toBe(false);
  expect(sameProviders([], [])).toBe(true);
});

test("every state has words", () => {
  for (const status of ["ready", "quota", "key", "model", "unreachable"]) {
    expect(statusLabel(provider(status), t, time)).not.toMatch(/^kh\./);
  }
  expect(statusLabel(provider("quota"), t, time)).toBe("Kontingent leer bis 9:00");
  expect(statusLabel(provider("ready"), t, time)).toBe("bereit");
});

test("ten free places with https addresses and a date", () => {
  expect(FREE_AI_KEYS).toHaveLength(10);
  for (const place of FREE_AI_KEYS) {
    expect(place.keyUrl).toMatch(/^https:\/\//);
    expect(place.baseUrl).toMatch(/^https:\/\//);
    expect(place.note.de).not.toBe("");
    expect(place.note.en).not.toBe("");
  }
  expect(new Set(FREE_AI_KEYS.map(place => place.name)).size).toBe(10);
  expect(FREE_AI_KEYS_DATE).toMatch(/^\d{4}-\d{2}-\d{2}$/);
});

test("kh.ai has the same keys in German and English", () => {
  expect(keys(de.kh.ai)).toEqual(keys(en.kh.ai));
});
