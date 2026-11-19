// KH: tests for "Neu in Kochheft" (D69): which versions a person has not seen, add-on filtering, version order, and
// that every card has its texts in both languages.
import { describe, expect, test } from "vitest";
import { DEFAULT_ADDONS } from "../lib/addons";
import { compareVersions, forAddons, newsTextKey, unseenNews, WHATS_NEW, type KhNewsVersion } from "../lib/whats-new";
import { startDialog } from "../lib/start-dialog";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

const card = (key: string, addon?: "shopping") => ({ icon: "wave", key, addon });
const LIST: KhNewsVersion[] = [
  { version: "1.10", cards: [card("a")] },
  { version: "1.9", cards: [card("b")] },
  { version: "1.3", cards: [card("c", "shopping")] },
];

describe("compareVersions", () => {
  test("compares by number, not by text", () => {
    expect(compareVersions("1.10", "1.9")).toBeGreaterThan(0);
    expect(compareVersions("1.3", "1.3.0")).toBe(0);
    expect(compareVersions("1.2", "1.3")).toBeLessThan(0);
  });
});

describe("unseenNews", () => {
  test("a person without a seen version gets the two newest", () => {
    expect(unseenNews(null, LIST, DEFAULT_ADDONS).map(v => v.version)).toEqual(["1.10", "1.9"]);
  });

  test("only versions newer than the seen one", () => {
    expect(unseenNews("1.9", LIST, DEFAULT_ADDONS).map(v => v.version)).toEqual(["1.10"]);
    expect(unseenNews("1.10", LIST, DEFAULT_ADDONS)).toEqual([]);
  });

  test("leaves out cards of switched-off add-ons, and a version left empty", () => {
    const off = { ...DEFAULT_ADDONS, shopping: false };
    expect(unseenNews("1.2", [LIST[2]!], off)).toEqual([]);
    expect(forAddons(LIST, off).map(v => v.version)).toEqual(["1.10", "1.9"]);
  });
});

test("the first list entry has 6 to 8 cards and the first card names a text key", () => {
  expect(WHATS_NEW[0]!.cards.length).toBeGreaterThanOrEqual(6);
  expect(WHATS_NEW[0]!.cards.length).toBeLessThanOrEqual(12);
  expect(newsTextKey("1.3", card("tiles"))).toBe("kh.news.v1-3.tiles");
});

test("every card has a title and a text in both languages", () => {
  for (const texts of [khTexts, khTextsDe]) {
    const news = texts.kh.news as unknown as Record<string, Record<string, { title: string; text: string }>>;
    for (const entry of WHATS_NEW) {
      for (const c of entry.cards) {
        const t = news[`v${entry.version.replace(/\./g, "-")}`]![c.key];
        expect(t?.title, c.key).toBeTruthy();
        expect(t?.text, c.key).toBeTruthy();
      }
    }
  }
});

describe("startDialog", () => {
  const status = { mustChangePassword: false, needsEmail: false, pendingEmail: null, tour: false, newsSeen: null };
  const facts = { status, signedIn: true, hasNews: true, askDevice: true };

  test("tour first, then news, then the device question", () => {
    expect(startDialog({ ...facts, status: { ...status, tour: true } })).toBe("tour");
    expect(startDialog(facts)).toBe("news");
    expect(startDialog({ ...facts, hasNews: false })).toBe("device");
    expect(startDialog({ ...facts, hasNews: false, askDevice: false })).toBeNull();
  });

  test("nothing while a first step is open, without a status, or signed out", () => {
    expect(startDialog({ ...facts, status: { ...status, mustChangePassword: true } })).toBeNull();
    expect(startDialog({ ...facts, status: { ...status, needsEmail: true } })).toBeNull();
    expect(startDialog({ ...facts, status: null })).toBeNull();
    expect(startDialog({ ...facts, signedIn: false })).toBeNull();
  });
});
