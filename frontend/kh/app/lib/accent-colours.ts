// KH: the ten accent colours a person or an installation can choose (wave 2), each with a light and a dark variant for
// Vuetify's primary and the hint tiles. Contrast is checked in __tests__/kh-accent.test.ts. Pure rules, no screen.
import { KH_HINT_COLORS } from "./theme";

export type KhAccent = "salbei" | "waldgruen" | "petrol" | "blau" | "indigo" | "lila" | "beere" | "tomatenrot" | "terrakotta" | "senf";

/** Light: primary (white text on it), hint surface and hint text. Dark: primary (dark text on it), that dark text, hint
 * surface (the primary at 16 % on the dark ground) and hint text. One line per colour: the server's manifest colour
 * (mealie/kh/accent.py) is read from the light primary by a test. */
export interface KhAccentColours {
  light: { primary: string; hint: string; onHint: string };
  dark: { primary: string; onPrimary: string; hint: string; onHint: string };
}

// Salbei is the look of every older installation: exactly the values of lib/theme.ts and the server's theme
export const KH_ACCENTS: Record<KhAccent, KhAccentColours> = {
  salbei: { light: { primary: "#2F7A55", hint: KH_HINT_COLORS.light["kh-hint"], onHint: KH_HINT_COLORS.light["on-kh-hint"] }, dark: { primary: "#4FB07E", onPrimary: "#0E1A13", hint: KH_HINT_COLORS.dark["kh-hint"], onHint: KH_HINT_COLORS.dark["on-kh-hint"] } },
  waldgruen: { light: { primary: "#207E47", hint: "#E9F2ED", onHint: "#1D7240" }, dark: { primary: "#2FBC6A", onPrimary: "#0E1B13", hint: "#21372A", onHint: "#2FBC6A" } },
  petrol: { light: { primary: "#187986", hint: "#E8F2F3", onHint: "#156E79" }, dark: { primary: "#31B3C4", onPrimary: "#0E191B", hint: "#213639", onHint: "#31B3C4" } },
  blau: { light: { primary: "#236DC7", hint: "#E9F0F9", onHint: "#1F61B2" }, dark: { primary: "#78A6DD", onPrimary: "#0E141B", hint: "#2C343D", onHint: "#78A6DD" } },
  indigo: { light: { primary: "#4044BF", hint: "#ECECF9", onHint: "#4044BF" }, dark: { primary: "#9C9EDE", onPrimary: "#0E0F1B", hint: "#32323D", onHint: "#9C9EDE" } },
  lila: { light: { primary: "#8946B9", hint: "#F3EDF8", onHint: "#8443B1" }, dark: { primary: "#BB94D6", onPrimary: "#150E1B", hint: "#37313B", onHint: "#BB94D6" } },
  beere: { light: { primary: "#C2387D", hint: "#F9EBF2", onHint: "#AE3270" }, dark: { primary: "#DD88B3", onPrimary: "#1B0E14", hint: "#3D2F36", onHint: "#DD88B3" } },
  tomatenrot: { light: { primary: "#CA382B", hint: "#FAEBEA", onHint: "#B53226" }, dark: { primary: "#E08C85", onPrimary: "#1B0F0E", hint: "#3D302E", onHint: "#E08C85" } },
  terrakotta: { light: { primary: "#A85A38", hint: "#F6EFEB", onHint: "#955032" }, dark: { primary: "#D29479", onPrimary: "#1B120E", hint: "#3B312D", onHint: "#D29479" } },
  senf: { light: { primary: "#8D6707", hint: "#F4F0E6", onHint: "#7E5C07" }, dark: { primary: "#C89D32", onPrimary: "#1B170E", hint: "#393221", onHint: "#C89D32" } },
};

/** The keys in the order the swatches are shown. */
export const KH_ACCENT_KEYS = Object.keys(KH_ACCENTS) as KhAccent[];

/** The key when it is one of the ten colours, else null. */
export function asKhAccent(value: string | null | undefined): KhAccent | null {
  return KH_ACCENT_KEYS.find(key => key === value) ?? null;
}

/** The colour to show: the person's choice, else the installation's; null when nobody chose one, so the theme the
 * operator configured (Salbei unless THEME_* says otherwise) stays. */
export function chooseAccent(person: string | null | undefined, installation: string | null | undefined): KhAccent | null {
  return asKhAccent(person) ?? asKhAccent(installation);
}

const CACHE_KEY = "kh-accent";

/** What the last start knew: the installation's colour and the colour of the last signed-in person (with their id,
 * so nobody else gets it). Kept in the browser so a start without a connection does not flip to another colour. */
export interface KhAccentCache {
  installation: KhAccent | null;
  person: { userId: string; accent: KhAccent | null } | null;
}

/** The cache from the storage; anything missing or broken counts as empty. */
export function readAccentCache(storage: Pick<Storage, "getItem">): KhAccentCache {
  try {
    const data = JSON.parse(storage.getItem(CACHE_KEY) ?? "null");
    const person = data?.person && typeof data.person.userId === "string" ? { userId: data.person.userId as string, accent: asKhAccent(data.person.accent) } : null;
    return { installation: asKhAccent(data?.installation), person };
  }
  catch {
    return { installation: null, person: null };
  }
}

/** Stores the cache; a blocked or full storage is ignored (the colour then simply comes from the server). */
export function writeAccentCache(storage: Pick<Storage, "setItem">, cache: KhAccentCache): void {
  try {
    storage.setItem(CACHE_KEY, JSON.stringify(cache));
  }
  catch {
    // no storage, no cache
  }
}

/** The person's own colour: the loaded one once their settings arrived, else the cached one while that person is the
 * one signed in (their settings could not be loaded yet, e.g. offline), else none. */
export function personAccent(
  loaded: { userId: string | null; accent: KhAccent | null },
  cached: KhAccentCache["person"],
  signedInUserId: string | null,
): KhAccent | null {
  if (loaded.userId) return loaded.accent;
  return cached && signedInUserId === cached.userId ? cached.accent : null;
}

/** The colours Vuetify's theme gets for the accent, per look (the theme's own keys). */
export function themeColours(accent: KhAccent) {
  const { light, dark } = KH_ACCENTS[accent];
  return {
    light: { "primary": light.primary, "kh-hint": light.hint, "on-kh-hint": light.onHint },
    dark: { "primary": dark.primary, "on-primary": dark.onPrimary, "kh-hint": dark.hint, "on-kh-hint": dark.onHint },
  };
}
