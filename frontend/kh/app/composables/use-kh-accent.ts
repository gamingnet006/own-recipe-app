// KH: the accent colour on the screen (wave 2): the installation's colour, the person's own choice on top, put into
// Vuetify's themes at once when either changes. The rules are in lib/accent-colours.ts.
import { computed, ref } from "vue";
import { khSidebar } from "./use-kh-sidebar";
import { asKhAccent, chooseAccent, personAccent, readAccentCache, themeColours, writeAccentCache, type KhAccent, type KhAccentCache } from "../lib/accent-colours";

const KH_ACCENT_URL = "/api/kh/onboarding/accent";
// An unreachable server must not hold the start of the app back for long
const KH_ACCENT_TIMEOUT_MS = 4000;

/** The installation's colour (null: none chosen yet or not known). */
export const khInstallationAccent = ref<KhAccent | null>(null);

/** The last signed-in person's colour from the previous start (see KhAccentCache). */
export const khCachedPerson = ref<KhAccentCache["person"]>(null);

/** The id of the signed-in person, set by the plugin. */
export const khSignedInUserId = ref<string | null>(null);

/** The colour that shows now: the person's own, else the installation's; null keeps the operator's theme. */
export const khAccent = computed(() =>
  chooseAccent(personAccent(khSidebar, khCachedPerson.value, khSignedInUserId.value), khInstallationAccent.value),
);

/** Takes over what the last start knew, so the first page already has the colour (also without a connection). */
export function seedKhAccentFromCache(storage: Pick<Storage, "getItem">): void {
  const cache = readAccentCache(storage);
  khInstallationAccent.value = cache.installation;
  khCachedPerson.value = cache.person;
}

/** Keeps what is known now for the next start. */
export function saveKhAccentCache(storage: Pick<Storage, "setItem">): void {
  const person = khSidebar.userId ? { userId: khSidebar.userId, accent: khSidebar.accent } : khCachedPerson.value;
  writeAccentCache(storage, { installation: khInstallationAccent.value, person });
}

/** Reads the installation's colour (public, so the login page has it too). A plain fetch like the theme's, because
 * this runs in a plugin before the request helper exists; a failure or timeout keeps the colour known from before. */
export async function loadKhInstallationAccent(): Promise<void> {
  try {
    const response = await fetch(KH_ACCENT_URL, { signal: AbortSignal.timeout(KH_ACCENT_TIMEOUT_MS) });
    khInstallationAccent.value = asKhAccent((await response.json()).accent);
  }
  catch {
    // keep what the cache gave
  }
}

type Themes = Record<string, { colors: Record<string, string> } | undefined>;

// The colours of the themes before the first accent was put in, to go back to the operator's theme
let original: Record<string, Record<string, string>> | null = null;

/** Writes the accent's colours into the two Vuetify themes (the theme object of vuetify.theme); null puts the theme
 * back as it was configured. */
export function applyKhAccent(themes: Themes, accent: KhAccent | null): void {
  const colours = themeColours(accent ?? "salbei");
  original ??= Object.fromEntries(
    (["light", "dark"] as const).map(look => [look, Object.fromEntries(Object.keys(colours[look]).map(key => [key, themes[look]?.colors[key] as string]))]),
  );
  for (const look of ["light", "dark"] as const) {
    const theme = themes[look];
    if (theme) theme.colors = { ...theme.colors, ...(accent ? colours[look] : original[look]) };
  }
}

/** Forgets the remembered theme (tests). */
export function resetKhAccentOriginal(): void {
  original = null;
}
