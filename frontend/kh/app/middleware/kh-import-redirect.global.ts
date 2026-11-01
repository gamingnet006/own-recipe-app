// KH: sends Mealie's import pages (phase 2) and the intake's old address (D38) to the intake on the drafts page, so
// no recipe is saved without a review.
// The query stays, so a link shared to the app (Mealie's recipe_import_url) still arrives.
import { importRedirectTarget } from "../composables/use-kh-drafts";

export default defineNuxtRouteMiddleware((to) => {
  const target = importRedirectTarget(to.path);
  if (target) {
    return navigateTo({ path: target, query: to.query });
  }
});
