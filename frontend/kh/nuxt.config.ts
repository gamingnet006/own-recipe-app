// KH: Küchenhelfer's own Nuxt layer (D26), mounted by one `extends` line in frontend/nuxt.config.ts.
// Our plugins, components and pages live in kh/app/, apart from Mealie's app/; our texts in kh/lang/.
import { defineNuxtConfig } from "nuxt/config";

export default defineNuxtConfig({
  i18n: {
    // Merged into Mealie's languages; the others fall back to English. Like in Mealie's config the
    // path starts in kh/i18n, so it goes one folder up.
    langDir: "./../lang",
    locales: [
      { code: "en-US", file: "en-US.json" },
      { code: "de-DE", file: "de-DE.json" },
    ],
  },
});
