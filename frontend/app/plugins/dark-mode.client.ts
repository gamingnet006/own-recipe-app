// KH: the look follows the three-way choice System / Hell / Dunkel (use-kh-theme.ts) instead of vueuse's two-way toggle;
// Vuetify gets the resolved look by name, so "System" also switches live when the device does.
import { useKhTheme } from "~~/kh/app/composables/use-kh-theme";

export default defineNuxtPlugin((nuxtApp) => {
  const { resolved } = useKhTheme();

  watch(resolved, (name) => {
    nuxtApp.vueApp.$nuxt.$vuetify?.theme.change(name);
  });

  nuxtApp.hook("vuetify:ready", (vuetify) => {
    vuetify.theme.change(resolved.value);
  });

  return {
    provide: {},
  };
});
