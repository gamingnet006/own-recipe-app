// KH: pure helpers of accounts without e-mail and the first steps (D53): placeholder addresses, the redirect to the
// first steps, and the server's error text.
import type { KhOnboardingStatus } from "./api/onboarding";

export const FIRST_STEPS_PATH = "/erste-schritte";

// Pages that must stay reachable while steps are open: the steps themselves, signing in or out, and the mail links.
const EXEMPT_PATHS = [FIRST_STEPS_PATH, "/login", "/logout", "/willkommen", "/email-bestaetigen"];

/** True for the made-up addresses of accounts without e-mail (and D52 linked accounts); they end in ".invalid". */
export function isPlaceholderEmail(email: string | null | undefined): boolean {
  return (email ?? "").toLowerCase().endsWith(".invalid");
}

/** The address to show: empty for placeholders, so people never see the made-up one. */
export function shownEmail(email: string | null | undefined): string {
  return !email || isPlaceholderEmail(email) ? "" : email;
}

/** Where a signed-in person must go first, or null when nothing is open or the page is exempt. */
export function onboardingRedirect(path: string, status: KhOnboardingStatus | null): string | null {
  if (!status || EXEMPT_PATHS.includes(path)) return null;
  return status.mustChangePassword || status.needsEmail ? FIRST_STEPS_PATH : null;
}

/** The server's own message of a failed request (its "detail"), or the fallback text. */
export function failureText(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
