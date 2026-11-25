// KH: which one dialog the start page opens for a signed-in person (D59, D68, D69): the tour for a new person, then
// the question about what the person does not tolerate, the news, then the new-address card (D85), then the question about setting this device up. Never more than one, so they do not pile up.
import type { KhOnboardingStatus } from "./api/onboarding";
import { shouldShowTour } from "./tour";

export type KhStartDialog = "tour" | "intolerances" | "news" | "address" | "device" | null;

export interface KhStartFacts {
  status: KhOnboardingStatus | null;
  signedIn: boolean;
  /** The add-on "Allergene" is on, so "Verträgst du etwas nicht?" makes sense. */
  allergensOn: boolean;
  /** There are news cards the person has not seen. */
  hasNews: boolean;
  /** The address changed and this person has not seen the card yet (see addressCardDue). */
  addressChanged: boolean;
  /** This device should be asked about its setup (see shouldAskDevice). */
  askDevice: boolean;
}

/** The dialog to open. Without a status, or while a first step (own password, e-mail address) is open, none. */
export function startDialog(facts: KhStartFacts): KhStartDialog {
  const { status, signedIn } = facts;
  if (!signedIn || !status || status.mustChangePassword || status.needsEmail) return null;
  if (shouldShowTour(status, signedIn)) return "tour";
  if (facts.allergensOn && !status.intolerancesAsked) return "intolerances";
  if (facts.hasNews) return "news";
  if (facts.addressChanged) return "address";
  return facts.askDevice ? "device" : null;
}
