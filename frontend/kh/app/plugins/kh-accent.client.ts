// KH: the accent colour (wave 2): takes over the colour of the last start, asks for the installation's colour before
// the first page (login page, setup), then keeps Vuetify's themes in step with the colour that shows (own choice, else
// the installation's, else the operator's theme) and remembers it for the next start.
import { applyKhAccent, khAccent, khInstallationAccent, khSignedInUserId, loadKhInstallationAccent, saveKhAccentCache, seedKhAccentFromCache } from "../composables/use-kh-accent";
import { khSidebar } from "../composables/use-kh-sidebar";

export default defineNuxtPlugin({
  async setup(nuxtApp) {
    const auth = useMealieAuth();
    watchEffect(() => {
      khSignedInUserId.value = auth.user.value?.id ?? null;
    });
    seedKhAccentFromCache(localStorage);
    await loadKhInstallationAccent();
    watch([khInstallationAccent, () => khSidebar.userId, () => khSidebar.accent], () => saveKhAccentCache(localStorage), { immediate: true });
    nuxtApp.hook("vuetify:ready", (vuetify) => {
      watch(khAccent, accent => applyKhAccent(vuetify.theme.themes.value, accent), { immediate: true });
    });
  },
});
