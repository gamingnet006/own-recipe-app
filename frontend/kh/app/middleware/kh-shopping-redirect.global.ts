// KH: sends Mealie's shopping list pages to the tile page (D60); "?klassisch=1" keeps Mealie's own page reachable.
import { shoppingRedirect } from "../lib/shopping-items";

export default defineNuxtRouteMiddleware((to) => {
  const target = shoppingRedirect(to.path, to.query);
  if (target) return navigateTo(target);
});
