import axios from "axios";
import { appName } from "~~/kh/app/lib/locale"; // KH: wave 2
import type { AppInfo } from "~/lib/api/types/admin";

export default defineNuxtPlugin({
  dependsOn: ["i18n:plugin"], // KH: the title follows the language (wave 2)
  async setup(nuxtApp) {
    const { data } = await axios.get<AppInfo>("/api/app/about");

    useHead({
      title: () => appName(data.brandingName, nuxtApp.$i18n.t("kh.app.name")), // KH: Kochheft or Cookbook (wave 2)
      link: data.brandingLogoUrl
        ? [
            { rel: "icon", href: data.brandingLogoUrl },
            { rel: "shortcut icon", href: data.brandingLogoUrl },
          ]
        : [],
    });

    return {
      provide: {
        appInfo: data,
      },
    };
  },
});
