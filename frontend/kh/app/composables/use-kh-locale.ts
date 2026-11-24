// KH: puts the language of the rules in lib/locale.ts on the screen, and stores a person's choice on their account.
// Outside a component (a route guard, a plugin) pass the app's i18n, because useI18n() would throw there.
import type { Composer } from "vue-i18n";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { chooseLocale, deviceLocale, type KhLocale } from "../lib/locale";
import { saveKhLocale } from "./use-kh-sidebar";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";

// The installation's language from the first setup; undefined until it was asked for once (only needed when the
// device speaks neither German nor English)
let installation: KhLocale | null | undefined;

async function installationLocale(i18n: Composer): Promise<KhLocale | null> {
  if (installation === undefined) {
    const { data } = await new KhOnboardingApi(useRequests(i18n)).installationLocale();
    installation = data ? data.locale : null;
  }
  return installation;
}

/** Shows the language the person gets: their account's choice if there is one, else the device's, else the
 * installation's (asked only then), else English. Nothing is stored. */
export async function applyKhLocale(account: KhLocale | null, i18n: Composer): Promise<void> {
  const device = deviceLocale(navigator.languages?.length ? navigator.languages : [navigator.language]);
  const needsInstallation = !account && !device;
  await i18n.setLocale(chooseLocale(account, device, needsInstallation ? await installationLocale(i18n) : null));
}

/** A person picked a language: shown at once, and kept on their account when signed in (every device then follows). */
export async function chooseKhLocale(locale: KhLocale, signedIn: boolean, i18n: Composer = useGlobalI18n()): Promise<void> {
  await i18n.setLocale(locale);
  if (signedIn) await saveKhLocale(locale);
}

/** Forgets the cached installation language (tests). */
export function resetKhLocale(): void {
  installation = undefined;
}
