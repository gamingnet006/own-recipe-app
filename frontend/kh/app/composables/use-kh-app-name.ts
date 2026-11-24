// KH: the name the app gives itself on screen: "Kochheft" in German, "Cookbook" in English (key kh.app.name), unless
// the installation sets its own BRANDING_NAME.
import { appName } from "../lib/locale";
import { useGlobalI18n } from "~/composables/use-global-i18n";

export function useKhAppName() {
  const { $appInfo } = useNuxtApp();
  const i18n = useGlobalI18n();
  return computed(() => appName($appInfo.brandingName, i18n.t("kh.app.name")));
}
