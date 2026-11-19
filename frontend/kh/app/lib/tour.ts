// KH: the first-sign-in tour (D59): its steps, which of them an add-on switch leaves out, and when it is shown.
import type { KhAddonFlags } from "./addons";
import type { KhOnboardingStatus } from "./api/onboarding";

export interface KhTourStep {
  /** Key of the texts under kh.tour.steps. */
  key: "welcome" | "recipes" | "intake" | "shopping" | "cook" | "more";
  /** Name of one of Mealie's icons ($globals.icons) */
  icon: string;
  /** The add-on that has to be on for the step to show. */
  addon?: keyof KhAddonFlags;
}

export const TOUR_STEPS: KhTourStep[] = [
  { key: "welcome", icon: "wave" },
  { key: "recipes", icon: "silverwareForkKnife" },
  { key: "intake", icon: "import" },
  { key: "shopping", icon: "formatListCheck", addon: "shopping" },
  { key: "cook", icon: "chefHat" },
  { key: "more", icon: "dotsHorizontal" },
];

/** The steps to show: those whose add-on is on (the shopping list can be switched off, D46). */
export function tourSteps(on: KhAddonFlags): KhTourStep[] {
  return TOUR_STEPS.filter(step => !step.addon || on[step.addon]);
}

/** Whether the start page shows the tour: somebody is signed in, the admin asked for it and no other first step (own
 * password, e-mail address) is open, which would send the person to /erste-schritte first. */
export function shouldShowTour(status: KhOnboardingStatus | null, signedIn: boolean): boolean {
  return signedIn && !!status && status.tour && !status.mustChangePassword && !status.needsEmail;
}
