// KH: puts the class "kh-simple" on the page while the person's simple view is on (D79); kh-theme.css makes the
// writing larger under it.
import { khSidebar } from "../composables/use-kh-sidebar";

export default defineNuxtPlugin(() => {
  watchEffect(() => document.documentElement.classList.toggle("kh-simple", khSidebar.simple));
});
