// KH: loads the person's own side-menu settings (D58) before the first page shows, so hidden entries never flash, and
// forgets them when nobody is signed in any more (a sign-out without reload). A route guard runs before any component
// exists: useI18n() would throw there (vue-i18n error 26), so it hands the app's own i18n instance on.
import type { Composer } from "vue-i18n";
// The person's chosen language (if any) is shown once per sign-in, so a language picked later is not overwritten.
import { applyKhLocale } from "../composables/use-kh-locale";
import { khSidebar, loadKhSidebarFor, resetKhSidebar } from "../composables/use-kh-sidebar";

let localeShownFor: string | null = null;

export default defineNuxtRouteMiddleware(async () => {
  const user = useMealieAuth().user.value;
  if (!user) {
    localeShownFor = null;
    return resetKhSidebar();
  }
  const i18n = useNuxtApp().$i18n as unknown as Composer;
  await loadKhSidebarFor(user.id, i18n);
  // only once the settings really loaded: after a failed (offline) start the retry still applies the account's language
  if (khSidebar.userId === user.id && localeShownFor !== user.id) {
    localeShownFor = user.id;
    await applyKhLocale(khSidebar.locale, i18n);
  }
});
