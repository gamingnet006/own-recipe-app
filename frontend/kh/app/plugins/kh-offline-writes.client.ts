// KH: one central place for "this needs the server": while Kochheft is offline, a write request is not sent but answered
// with one clear note, instead of a generic error from every button.
import { isKhOnline } from "../composables/use-kh-connection";
import { needsServer } from "../lib/connection";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

export default defineNuxtPlugin((nuxtApp) => {
  // after all plugins ran, so that Mealie's own axios plugin exists and this hook runs before its response handling
  nuxtApp.hook("app:created", () => {
    nuxtApp.$axios.interceptors.request.use((config) => {
      if (isKhOnline() || !needsServer(config.method, config.url)) return config;
      config.suppressAlert = true; // Mealie's generic failure notice would only repeat it
      alert.error(useGlobalI18n().t("kh.connection.needs"));
      return Promise.reject(Object.assign(new Error("Needs a connection"), { config }));
    });
  });
});
