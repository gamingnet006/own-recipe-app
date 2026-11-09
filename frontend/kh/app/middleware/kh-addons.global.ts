// KH: pages of a switched-off add-on (D46) go back to the recipes with a hint, instead of showing a half-working page.
// A route guard runs before any component exists: useI18n() would throw there (vue-i18n error 26), so it uses the
// app's own i18n instance.
import { addonRedirect } from "../lib/addons";
import { khAddons, loadKhAddonsFor } from "../composables/use-kh-addons";
import type { Composer } from "vue-i18n";
import { alert } from "~/composables/use-toast";

export default defineNuxtRouteMiddleware(async (to) => {
  const user = useMealieAuth().user.value;
  if (!user) return;
  const i18n = useNuxtApp().$i18n as unknown as Composer;
  await loadKhAddonsFor(user.id, i18n);
  const redirect = addonRedirect(to.path, khAddons.enabled, user.groupSlug);
  if (!redirect) return;
  alert.warning(i18n.t("kh.addons.off-hint", { name: i18n.t(`kh.addons.names.${redirect.addon}`) }));
  return navigateTo(redirect.to);
});
