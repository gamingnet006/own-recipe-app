// KH: tests for "Neu in Kochheft" (D69): which versions a person has not seen, add-on filtering, version order, and
// that every card has its texts in both languages.
import { describe, expect, test } from "vitest";
import { DEFAULT_ADDONS } from "../lib/addons";
import { compareVersions, forAddons, newsTextKey, unseenNews, WHATS_NEW, type KhNewsVersion } from "../lib/whats-new";
import { addressCardDue } from "../lib/address-change";
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

test("admin cards show to admins only, and a version of nothing else is dropped for the others", () => {
  const admin: KhNewsVersion[] = [{ version: "1.4", cards: [{ icon: "autoFix", key: "wizard", admin: true }] }];
  expect(forAddons(admin, DEFAULT_ADDONS)).toEqual([]);
  expect(forAddons(admin, DEFAULT_ADDONS, true)).toEqual(admin);
  expect(unseenNews(null, admin, DEFAULT_ADDONS)).toEqual([]);
  expect(unseenNews(null, admin, DEFAULT_ADDONS, true)).toEqual(admin);
});

test("the first list entry has 3 to 12 cards and the first card names a text key", () => {
  expect(WHATS_NEW[0]!.cards.length).toBeGreaterThanOrEqual(3);
  expect(WHATS_NEW[0]!.cards.length).toBeLessThanOrEqual(12);
  expect(newsTextKey("1.4", card("simple"))).toBe("kh.news.v1-4.simple");
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
  const status = { mustChangePassword: false, needsEmail: false, pendingEmail: null, tour: false, newsSeen: null, intolerancesAsked: true };
  const facts = { status, signedIn: true, hasNews: true, addressChanged: true, askDevice: true, allergensOn: true };

  test("tour first, then the intolerance question (once, only with the allergen add-on), then news", () => {
    const open = { ...status, tour: true, intolerancesAsked: false };
    expect(startDialog({ ...facts, status: open })).toBe("tour");
    expect(startDialog({ ...facts, status: { ...open, tour: false } })).toBe("intolerances");
    expect(startDialog({ ...facts, status: { ...open, tour: false }, allergensOn: false })).toBe("news");
    expect(startDialog(facts)).toBe("news");
  });

  test("tour first, then news, then the device question", () => {
    expect(startDialog({ ...facts, status: { ...status, tour: true } })).toBe("tour");
    expect(startDialog(facts)).toBe("news");
    expect(startDialog({ ...facts, hasNews: false })).toBe("address");
    expect(startDialog({ ...facts, hasNews: false, addressChanged: false })).toBe("device");
    expect(startDialog({ ...facts, hasNews: false, addressChanged: false, askDevice: false })).toBeNull();
  });

  test("nothing while a first step is open, without a status, or signed out", () => {
    expect(startDialog({ ...facts, status: { ...status, mustChangePassword: true } })).toBeNull();
    expect(startDialog({ ...facts, status: { ...status, needsEmail: true } })).toBeNull();
    expect(startDialog({ ...facts, status: null })).toBeNull();
    expect(startDialog({ ...facts, signedIn: false })).toBeNull();
  });
});

describe("addressCardDue", () => {
  test("only for a change the person has not seen", () => {
    expect(addressCardDue(null, null)).toBe(false);
    expect(addressCardDue("2026-11-01T10:00", null)).toBe(true);
    expect(addressCardDue("2026-11-01T10:00", "2026-11-01T10:00")).toBe(false);
    expect(addressCardDue("2026-12-01T10:00", "2026-11-01T10:00")).toBe(true);
  });
});
