// KH: starts watching the browser's online/offline events once for the whole app (D63), so that the "no connection"
// state also ends on pages without the default layout.
import { watchBrowserConnection } from "../composables/use-kh-connection";

export default defineNuxtPlugin(() => {
  watchBrowserConnection();
});
