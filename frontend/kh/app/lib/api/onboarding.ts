// KH: the API of accounts without e-mail, first sign-in and the welcome and verification mails (D53) as a Mealie API
// class; the types are written by hand like the accounts' (mealie/kh/onboarding).
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { KhLocale } from "../locale";
import { OWN_ERRORS } from "./own-errors";

export interface KhOnboardingStatus {
  mustChangePassword: boolean;
  needsEmail: boolean;
  pendingEmail: string | null;
  /** The first-sign-in tour is still to be shown (D59). */
  tour: boolean;
  /** The newest "Neu in Kochheft" version the person has seen; null: none yet (D69). */
  newsSeen: string | null;
}

export interface KhWelcomeInfo {
  username: string;
  fullName: string;
}

export interface KhAccountSettings {
  emailRequired: boolean;
  /** The installation's language from the first setup; null until one was chosen. */
  locale: KhLocale | null;
}

const prefix = "/api/kh/onboarding";

export class KhOnboardingApi extends BaseAPI {
  /** What the signed-in person still has to do. */
  async me() {
    return await this.requests.get<KhOnboardingStatus>(`${prefix}/me`);
  }

  /** Sets the own password; the answer carries the new session token, because all older sessions end. */
  async setPassword(password: string) {
    return await this.requests.post<{ access_token: string; token_type: string }>(`${prefix}/password`, { password }, OWN_ERRORS);
  }

  /** Sends a verification mail to the address. */
  async requestEmail(email: string) {
    return await this.requests.post<unknown>(`${prefix}/email`, { email }, OWN_ERRORS);
  }

  /** Public: confirms the address with the token from the mail. */
  async confirmEmail(token: string) {
    return await this.requests.post<unknown>(`${prefix}/confirm-email`, { token }, OWN_ERRORS);
  }

  /** Public: who the welcome link is for. */
  async welcomeInfo(token: string) {
    return await this.requests.get<KhWelcomeInfo>(`${prefix}/welcome?token=${encodeURIComponent(token)}`);
  }

  /** Public: sets the first password with the token from the welcome mail. */
  async acceptWelcome(token: string, password: string) {
    return await this.requests.post<unknown>(`${prefix}/welcome`, { token, password }, OWN_ERRORS);
  }

  /** The person finished or skipped the first-sign-in tour. */
  async tourDone() {
    return await this.requests.post<unknown>(`${prefix}/tour-done`, {}, OWN_ERRORS);
  }

  /** The person finished or skipped "Neu in Kochheft" up to this version. */
  async newsSeen(version: string) {
    return await this.requests.post<unknown>(`${prefix}/news-seen`, { version }, OWN_ERRORS);
  }

  /** Admin: shows or hides the first-sign-in tour of a user. */
  async setTour(userId: string, tour: boolean) {
    return await this.requests.post<unknown>(`/api/kh/admin/onboarding/${userId}/tour`, { tour }, OWN_ERRORS);
  }

  /** Admin: the account settings. */
  async getSettings() {
    return await this.requests.get<KhAccountSettings>("/api/kh/admin/account-settings");
  }

  /** Admin: changes the account settings. */
  async putSettings(emailRequired: boolean) {
    return await this.requests.put<KhAccountSettings>("/api/kh/admin/account-settings", { emailRequired }, OWN_ERRORS);
  }

  /** Admin: saves the installation's language (the e-mail switch stays as it is). */
  async putLocale(locale: KhLocale) {
    return await this.requests.put<KhAccountSettings>("/api/kh/admin/account-settings", { locale }, OWN_ERRORS);
  }

  /** Public: the installation's language, null until the first setup chose one. */
  async installationLocale() {
    return await this.requests.get<{ locale: KhLocale | null }>(`${prefix}/locale`);
  }
}
