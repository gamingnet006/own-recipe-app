// KH: Küchenhelfer's own Nuxt layer (D26), mounted by one `extends` line in frontend/nuxt.config.ts.
// Our plugins, components and pages live in kh/app/, apart from Mealie's app/; our texts in kh/lang/.
import { fileURLToPath } from "node:url";
import { defineNuxtConfig } from "nuxt/config";
import { offlineCaching } from "./app/lib/offline";

export default defineNuxtConfig({
  // The font of the look "Salbei" (D38); a path from this layer, because "~" is Mealie's app folder
  // and the family cookbook's printout (D43)
  css: [
    fileURLToPath(new URL("./app/assets/kh-theme.css", import.meta.url)),
    fileURLToPath(new URL("./app/assets/kh-print.css", import.meta.url)),
  ],
  i18n: {
    // Merged into Mealie's languages; the others fall back to English. Like in Mealie's config the
    // path starts in kh/i18n, so it goes one folder up.
    langDir: "./../lang",
    locales: [
      { code: "en-US", file: "en-US.json" },
      { code: "de-DE", file: "de-DE.json" },
    ],
  },
  // The last recipes and their photos stay available offline (D42); merged into Mealie's workbox settings
  pwa: { workbox: { runtimeCaching: offlineCaching() } },
});
