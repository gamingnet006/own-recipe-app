// KH: the language before anybody has signed in: the browser's German or English, else English (an installation that
// chose a language in its first setup is used when the browser speaks neither). The account's choice replaces it
// after sign-in (middleware/kh-sidebar.global.ts). Replaces Mealie's own browser-language detection.
import type { Composer } from "vue-i18n";
import { applyKhLocale } from "../composables/use-kh-locale";

export default defineNuxtPlugin({
  dependsOn: ["i18n:plugin"],
  async setup(nuxtApp) {
    await applyKhLocale(null, nuxtApp.$i18n as unknown as Composer);
  },
});
