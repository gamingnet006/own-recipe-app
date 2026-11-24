// KH: which language a person sees (wave 2): only German and English. The account's choice wins, then the device's
// language, then the installation's, then English. Pure rules, no screen.

export type KhLocale = "de-DE" | "en-US";

/** The two languages Kochheft offers; names are written in their own language. */
export const KH_LOCALES: { value: KhLocale; name: string }[] = [
  { value: "de-DE", name: "Deutsch" },
  { value: "en-US", name: "English" },
];

/** English is what everybody sees when nothing else is known (fresh install, foreign browser language). */
export const FALLBACK_LOCALE: KhLocale = "en-US";

/** The value when it is one of the two languages, else null. */
export function asKhLocale(value: string | null | undefined): KhLocale | null {
  return KH_LOCALES.find(locale => locale.value === value)?.value ?? null;
}

/** The first German or English entry of the browser's language list ("de-AT" counts as German), else null. */
export function deviceLocale(languages: readonly string[]): KhLocale | null {
  for (const language of languages) {
    const base = language.toLowerCase().split("-")[0];
    if (base === "de") return "de-DE";
    if (base === "en") return "en-US";
  }
  return null;
}

/** The language to show: the account's choice, else the device's, else the installation's, else English. */
export function chooseLocale(account: string | null | undefined, device: KhLocale | null, installation: KhLocale | null): KhLocale {
  return asKhLocale(account) ?? device ?? installation ?? FALLBACK_LOCALE;
}

/** The configured name when it is Kochheft's default, so the translated name ("Kochheft" or "Cookbook") shows; an own
 * BRANDING_NAME is shown as it is. */
export function appName(configured: string, translated: string): string {
  return configured === "Kochheft" ? translated : configured;
}
