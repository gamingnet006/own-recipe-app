// KH: tests for the bell (D39): each notice in the words of the spec, with and without the provider taken next, which
// new notice the short hint shows, and the texts in both languages.
import { expect, test } from "vitest";
import { noticeText, oneAtATime, openBell, toastNotice } from "../composables/use-kh-notices";
import type { KhNotice } from "../lib/api/notices";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

/** A tiny i18n: looks a key up in TEXTS and fills in {placeholders}. */
function lookup(texts: object, key: string, values: Record<string, string> = {}): string {
  const text = key.split(".").reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], texts);
  return typeof text === "string" ? text.replace(/\{(\w+)\}/g, (_, name: string) => values[name] ?? "") : key;
}
const tDe = (key: string, values?: Record<string, string>) => lookup(de, key, values);
const tEn = (key: string, values?: Record<string, string>) => lookup(en, key, values);

/** Hours and minutes as in Germany in winter (UTC+1). */
const time = (d: Date) => `${d.getUTCHours() + 1}:${String(d.getUTCMinutes()).padStart(2, "0")}`;

/** Every key path in a nested texts object, sorted. */
function keys(node: object, prefix = ""): string[] {
  return Object.entries(node)
    .flatMap(([key, value]) => (typeof value === "object" ? keys(value, `${prefix}${key}.`) : [`${prefix}${key}`]))
    .sort();
}

function n(id: string, fields: Partial<KhNotice> = {}): KhNotice {
  return { id, kind: "ai_none", provider: null, nextProvider: null, until: null, createdAt: "2026-11-04T08:00:00Z", ...fields };
}

test("each kind reads as in the spec, with and without the next provider", () => {
  const quota = n("1", { kind: "ai_quota", provider: "Gemini", nextProvider: "Groq", until: "2026-11-04T08:00:00Z" });
  expect(noticeText(quota, tDe, time)).toBe("Gemini: Kontingent aufgebraucht bis 9:00. Ich nehme jetzt Groq.");
  expect(noticeText({ ...quota, nextProvider: null }, tDe, time)).toBe("Gemini: Kontingent aufgebraucht bis 9:00.");
  expect(noticeText(n("2", { kind: "ai_key", provider: "Mistral", nextProvider: "Cerebras" }), tDe, time))
    .toBe("Mistral: Schlüssel ungültig, übersprungen. Ich nehme jetzt Cerebras.");
  expect(noticeText(n("3", { kind: "ai_model", provider: "Groq" }), tDe, time)).toBe("Groq: Modell nicht gefunden.");
  expect(noticeText(n("4", { kind: "ai_unreachable", provider: "Gemini" }), tDe, time)).toBe("Gemini: nicht erreichbar.");
  expect(noticeText(n("5", { kind: "ai_ready", provider: "Gemini" }), tDe, time)).toBe("Gemini ist wieder bereit.");
  expect(noticeText(n("6"), tDe, time)).toBe("Keine KI erreichbar.");
  expect(noticeText(quota, tEn, time)).toBe("Gemini: quota used up until 9:00. Now using Groq.");
});

test("the short hint shows the newest of the new notices", () => {
  // newest first: during an outage the hint says "no AI reachable", not an older switch
  expect(toastNotice([n("3"), n("2"), n("1")], new Set(["1"]))).toEqual(n("3"));
  expect(toastNotice([n("1")], new Set(["1"]))).toBeUndefined();
});

test("a check while one is running is dropped, a later one runs", async () => {
  let calls = 0;
  let finish = () => {};
  const load = oneAtATime(() => {
    calls++;
    return new Promise<void>(resolve => (finish = resolve));
  });
  const first = load();
  await load(); // opening the app also reports it visible: the second check must not ask again
  expect(calls).toBe(1);
  finish();
  await first;
  const later = load();
  finish();
  await later;
  expect(calls).toBe(2);
});

test("opening the bell fetches what is new before marking it read", async () => {
  // else a notice from after the last check would count as read without being seen
  const steps: string[] = [];
  await openBell(async () => { steps.push("fetch"); }, async () => { steps.push("read"); });
  expect(steps).toEqual(["fetch", "read"]);
});

test("kh.notices has the same keys in German and English", () => {
  expect(keys(de.kh.notices)).toEqual(keys(en.kh.notices));
});

test("the draft error ai_unavailable and the intake hint have words in both languages", () => {
  for (const texts of [de, en]) {
    expect(texts.kh.drafts.error.ai_unavailable).toBeTruthy();
    expect(texts.kh.ai["unavailable-hint"]).toBeTruthy();
  }
});
