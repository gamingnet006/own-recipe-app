// KH: the first steps of a signed-in person (D53) as one shared state: the status (cached until a step is done or the
// user changes) and the steps themselves. Choosing a password ends every older session, so its new token is set first.
import { reactive } from "vue";
import { failureText } from "../lib/onboarding";
import { type KhOnboardingStatus, KhOnboardingApi } from "../lib/api/onboarding";
import { useRequests } from "~/composables/api/api-client";
import { useAuthBackend } from "~/composables/use-auth-backend";
import type { Composer } from "vue-i18n";

export const khOnboarding = reactive({ status: null as KhOnboardingStatus | null, userId: "" });

/** I18N: the app's own instance, needed in a route guard, where useI18n() throws (vue-i18n error 26). */
export function useKhOnboarding(i18n?: Composer) {
  const api = () => new KhOnboardingApi(useRequests(i18n));

  /** Reads the status from the server; a failed request is logged and leaves the app unblocked. */
  async function refresh(): Promise<void> {
    const { data, error } = await api().me();
    if (error) console.error("Kochheft: first-steps status not loaded", error);
    khOnboarding.status = data ?? null;
  }

  /** Loads the status once per user. */
  async function loadFor(userId: string): Promise<void> {
    if (khOnboarding.userId === userId) return;
    khOnboarding.userId = userId;
    await refresh();
  }

  /** Forgets the cached status (another person signed in, or a mail link was used). */
  function reset(): void {
    khOnboarding.userId = "";
    khOnboarding.status = null;
  }

  /** Sets the own password and the new token; returns the server's error text (or the fallback), null on success. */
  async function setPassword(password: string, fallback: string): Promise<string | null> {
    const { data, error } = await api().setPassword(password);
    if (!data) return failureText(error, fallback);
    useAuthBackend().setToken(data.access_token);
    await refresh();
    return null;
  }

  /** Asks for a verification mail; returns the server's error text (or the fallback), null on success. */
  async function requestEmail(email: string, fallback: string): Promise<string | null> {
    const { error } = await api().requestEmail(email);
    if (error) return failureText(error, fallback);
    await refresh();
    return null;
  }

  return { refresh, loadFor, reset, setPassword, requestEmail };
}
