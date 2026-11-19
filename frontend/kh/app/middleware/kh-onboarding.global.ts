// KH: a signed-in person with open first steps (own password, e-mail address) goes to /erste-schritte first (D53).
// The status is cached per user; a failed request must not block the app. A route guard runs before any component
// exists, so it hands the app's own i18n instance on (useI18n() would throw there, vue-i18n error 26).
import { onboardingRedirect } from "../lib/onboarding";
import { khOnboarding, useKhOnboarding } from "../composables/use-kh-onboarding";
import type { Composer } from "vue-i18n";

export default defineNuxtRouteMiddleware(async (to) => {
  const user = useMealieAuth().user.value;
  const onboarding = useKhOnboarding(useNuxtApp().$i18n as unknown as Composer);
  if (!user) return onboarding.reset(); // signed out without a reload: the next person starts without this status
  await onboarding.loadFor(user.id);
  const redirect = onboardingRedirect(to.path, khOnboarding.status);
  if (redirect) return navigateTo(redirect);
});
