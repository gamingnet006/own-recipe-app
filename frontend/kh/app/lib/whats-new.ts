// KH: "Neu in Kochheft" (D69): the cards per version, newest first, and which of them a person has not seen yet.
// Before a release with new functions add its cards here and raise NEWS_VERSION in mealie/kh/onboarding/news.py.
import type { KhAddonFlags } from "./addons";

export interface KhNewsCard {
  /** Name of one of Mealie's icons ($globals.icons). */
  icon: string;
  /** Key of the texts kh.news.<version>.<key>.{title,text}; dots in the version become dashes (v1-3). */
  key: string;
  /** The add-on that has to be on for the card to show. */
  addon?: keyof KhAddonFlags;
  /** A button on the card; "setup" opens the setup page. */
  action?: "setup";
}

export interface KhNewsVersion {
  version: string;
  cards: KhNewsCard[];
}

export const WHATS_NEW: KhNewsVersion[] = [
  {
    version: "1.3",
    cards: [
      { icon: "formatListCheck", key: "tiles", addon: "shopping" },
      { icon: "createAlt", key: "amount", addon: "shopping" },
      { icon: "cartCheck", key: "offline", addon: "shopping" },
      { icon: "microphone", key: "siri", addon: "shopping" },
      { icon: "shareVariant", key: "share" },
      { icon: "import", key: "files" },
      { icon: "calendarWeekBegin", key: "week", addon: "planner" },
      { icon: "star", key: "wishes", addon: "planner" },
      { icon: "shareVariant", key: "weekshare", addon: "planner" },
      { icon: "bellOutline", key: "notifications" },
      { icon: "cellphone", key: "setup", action: "setup" },
    ],
  },
];

/** The texts of a version live under a key without dots, because a dot would nest the JSON. */
export function newsTextKey(version: string, card: KhNewsCard): string {
  return `kh.news.v${version.replace(/\./g, "-")}.${card.key}`;
}

/** Compares "1.10" and "1.9" by number: negative when A is older than B. */
export function compareVersions(a: string, b: string): number {
  const left = a.split(".").map(Number);
  const right = b.split(".").map(Number);
  for (let i = 0; i < Math.max(left.length, right.length); i++) {
    const diff = (left[i] ?? 0) - (right[i] ?? 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

/** LIST without the cards of switched-off add-ons; a version left with no card is dropped. */
export function forAddons(list: KhNewsVersion[], on: KhAddonFlags): KhNewsVersion[] {
  return list
    .map(entry => ({ ...entry, cards: entry.cards.filter(card => !card.addon || on[card.addon]) }))
    .filter(entry => entry.cards.length > 0);
}

/** What a person has not seen: the versions newer than NEWS_SEEN (null: all), at most the two newest, newest first,
 * without cards of switched-off add-ons. */
export function unseenNews(newsSeen: string | null, list: KhNewsVersion[], on: KhAddonFlags): KhNewsVersion[] {
  const newer = list.filter(entry => newsSeen === null || compareVersions(entry.version, newsSeen) > 0);
  return forAddons(newer, on)
    .sort((a, b) => compareVersions(b.version, a.version))
    .slice(0, 2);
}
