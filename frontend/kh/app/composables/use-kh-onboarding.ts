// KH: the first steps of a signed-in person (D53) as one shared state: the status (cached until a step is done or the
// user changes) and the steps themselves. Choosing a password ends every older session, so its new token is set first.
import { reactive } from "vue";
import { failureText } from "../lib/onboarding";
import { type KhOnboardingStatus, KhOnboardingApi } from "../lib/api/onboarding";
import { useRequests } from "~/composables/api/api-client";
import { useAuthBackend } from "~/composables/use-auth-backend";
import { alert } from "~/composables/use-toast";
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

  /** The tour was finished or skipped: tells the server and takes the flag out of the cached status, so it does
   * not come back on the next visit of the start page. A failed request is reported. */
  async function finishTour(fallback: string): Promise<void> {
    if (khOnboarding.status) khOnboarding.status = { ...khOnboarding.status, tour: false };
    const { error } = await api().tourDone();
    if (error) alert.error(failureText(error, fallback));
  }

  /** "Neu in Kochheft" was finished or skipped: remembers VERSION on the server and in the cached status. */
  async function finishNews(version: string, fallback: string): Promise<void> {
    if (khOnboarding.status) khOnboarding.status = { ...khOnboarding.status, newsSeen: version };
    const { error } = await api().newsSeen(version);
    if (error) alert.error(failureText(error, fallback));
  }

  /** The question "Verträgst du etwas nicht?" was answered or skipped: tells the server and takes it out of the cached
   * status, so the start page does not ask again. A failed request is reported. */
  async function finishIntolerances(fallback: string): Promise<void> {
    if (khOnboarding.status) khOnboarding.status = { ...khOnboarding.status, intolerancesAsked: true };
    const { error } = await api().intolerancesAsked();
    if (error) alert.error(failureText(error, fallback));
  }

  /** The admin who just finished the first setup is new to Kochheft too: the tour at the start page instead of news
   * about versions they never knew (D83). Failures are reported; the status is read again either way. */
  async function introduceFirstAdmin(userId: string, newsVersion: string, fallback: string): Promise<void> {
    // one after the other: each may create the person's first onboarding row, and two at once collide
    const tour = await api().setTour(userId, true);
    const news = await api().newsSeen(newsVersion);
    const error = tour.error ?? news.error;
    if (error) alert.error(failureText(error, fallback));
    await refresh();
  }

  return { refresh, loadFor, reset, setPassword, requestEmail, finishTour, finishNews, finishIntolerances, introduceFirstAdmin };
}
