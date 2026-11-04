// KH: tests for the bell (D39): each notice in the words of the spec, with and without the provider taken next, which
// notices are new since the last check, and the texts in both languages.
import { expect, test } from "vitest";
import { freshNotices, noticeText } from "../composables/use-kh-notices";
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

test("only notices not seen before are fresh", () => {
  expect(freshNotices([n("1"), n("2")], new Set(["1"]))).toEqual([n("2")]);
  expect(freshNotices([n("1")], new Set(["1"]))).toEqual([]);
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
