// KH: pages of a switched-off add-on (D46) go back to the recipes with a hint, instead of showing a half-working page.
import { addonRedirect } from "../lib/addons";
import { khAddons, loadKhAddonsFor } from "../composables/use-kh-addons";
import { alert } from "~/composables/use-toast";

export default defineNuxtRouteMiddleware(async (to) => {
  const user = useMealieAuth().user.value;
  if (!user) return;
  await loadKhAddonsFor(user.id);
  const redirect = addonRedirect(to.path, khAddons.enabled, user.groupSlug);
  if (!redirect) return;
  const i18n = useGlobalI18n();
  alert.warning(i18n.t("kh.addons.off-hint", { name: i18n.t(`kh.addons.names.${redirect.addon}`) }));
  return navigateTo(redirect.to);
});
