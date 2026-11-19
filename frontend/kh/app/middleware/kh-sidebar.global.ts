// KH: loads the person's own side-menu settings (D58) before the first page shows, so hidden entries never flash, and
// forgets them when nobody is signed in any more (a sign-out without reload). A route guard runs before any component
// exists: useI18n() would throw there (vue-i18n error 26), so it hands the app's own i18n instance on.
import type { Composer } from "vue-i18n";
import { loadKhSidebarFor, resetKhSidebar } from "../composables/use-kh-sidebar";

export default defineNuxtRouteMiddleware(async () => {
  const user = useMealieAuth().user.value;
  if (!user) return resetKhSidebar();
  await loadKhSidebarFor(user.id, useNuxtApp().$i18n as unknown as Composer);
});
