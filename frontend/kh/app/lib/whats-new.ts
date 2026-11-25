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
  /** Only admins see the card (D83). */
  admin?: boolean;
  /** A button on the card: "setup" opens the device setup page, "wizard" the first-time setup (D83). */
  action?: "setup" | "wizard";
}

export interface KhNewsVersion {
  version: string;
  cards: KhNewsCard[];
}

export const WHATS_NEW: KhNewsVersion[] = [
  {
    version: "1.5",
    cards: [
      { icon: "translate", key: "language" },
      { icon: "cog", key: "settings" },
      { icon: "palette", key: "colour" },
      { icon: "microphone", key: "siri", addon: "shopping" },
      { icon: "tags", key: "tags" },
      { icon: "download", key: "offline" },
      { icon: "group", key: "kinds", admin: true },
    ],
  },
  {
    version: "1.4",
    cards: [
      { icon: "eye", key: "simple" },
      { icon: "foods", key: "season", addon: "season" },
      { icon: "qrCode", key: "qr", addon: "shopping", action: "setup" },
      { icon: "noteTextOutline", key: "note" },
      { icon: "autoFix", key: "wizard", admin: true, action: "wizard" },
    ],
  },
  {
    version: "1.3",
    cards: [
      { icon: "formatListCheck", key: "tiles", addon: "shopping" },
      { icon: "microphone", key: "siri", addon: "shopping" },
      { icon: "shareVariant", key: "share" },
      { icon: "calendarWeekBegin", key: "week", addon: "planner" },
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

/** LIST without the cards of switched-off add-ons and, unless IS_ADMIN, the admin cards; a version left with no card is
 * dropped. */
export function forAddons(list: KhNewsVersion[], on: KhAddonFlags, isAdmin = false): KhNewsVersion[] {
  return list
    .map(entry => ({
      ...entry,
      cards: entry.cards.filter(card => (!card.addon || on[card.addon]) && (!card.admin || isAdmin)),
    }))
    .filter(entry => entry.cards.length > 0);
}

/** What a person has not seen: the versions newer than NEWS_SEEN (null: all), at most the two newest, newest first,
 * without cards of switched-off add-ons or (for non-admins) admin cards. */
export function unseenNews(newsSeen: string | null, list: KhNewsVersion[], on: KhAddonFlags, isAdmin = false): KhNewsVersion[] {
  const newer = list.filter(entry => newsSeen === null || compareVersions(entry.version, newsSeen) > 0);
  return forAddons(newer, on, isAdmin)
    .sort((a, b) => compareVersions(b.version, a.version))
    .slice(0, 2);
}
