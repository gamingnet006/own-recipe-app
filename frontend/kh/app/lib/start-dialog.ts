// KH: which one dialog the start page opens for a signed-in person (D59, D68, D69): the tour for a new person, then
// the news, then the question about setting this device up. Never more than one, so they do not pile up.
import type { KhOnboardingStatus } from "./api/onboarding";
import { shouldShowTour } from "./tour";

export type KhStartDialog = "tour" | "news" | "device" | null;

export interface KhStartFacts {
  status: KhOnboardingStatus | null;
  signedIn: boolean;
  /** There are news cards the person has not seen. */
  hasNews: boolean;
  /** This device should be asked about its setup (see shouldAskDevice). */
  askDevice: boolean;
}

/** The dialog to open. Without a status, or while a first step (own password, e-mail address) is open, none. */
export function startDialog(facts: KhStartFacts): KhStartDialog {
  const { status, signedIn } = facts;
  if (!signedIn || !status || status.mustChangePassword || status.needsEmail) return null;
  if (shouldShowTour(status, signedIn)) return "tour";
  if (facts.hasNews) return "news";
  return facts.askDevice ? "device" : null;
}
