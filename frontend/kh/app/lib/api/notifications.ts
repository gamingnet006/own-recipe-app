// KH: the API of "Mitteilungen" (D75) as a Mealie API class; types by hand like the other KH ones (mealie/kh/notifications).
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { KhNotificationSettings } from "../notifications";
import { OWN_ERRORS } from "./own-errors";

export interface KhPushDevice {
  id: string;
  endpoint: string;
  userAgent: string;
  createdAt: string | null;
  lastOkAt: string | null;
}

const prefix = "/api/kh/notifications";

export class KhNotificationsApi extends BaseAPI {
  /** The server's public key for pushManager.subscribe. */
  async key() {
    return await this.requests.get<{ key: string }>(`${prefix}/key`);
  }

  async settings() {
    return await this.requests.get<KhNotificationSettings>(`${prefix}/settings`);
  }

  async putSettings(settings: KhNotificationSettings) {
    return await this.requests.put<KhNotificationSettings>(`${prefix}/settings`, settings, OWN_ERRORS);
  }

  async devices() {
    return await this.requests.get<KhPushDevice[]>(`${prefix}/subscriptions`);
  }

  /** Adds this device; SUBSCRIPTION is PushSubscription.toJSON(). */
  async subscribe(subscription: PushSubscriptionJSON) {
    return await this.requests.post<unknown>(`${prefix}/subscriptions`, subscription, OWN_ERRORS);
  }

  async unsubscribe(endpoint: string) {
    return await this.requests.delete<unknown>(`${prefix}/subscriptions?endpoint=${encodeURIComponent(endpoint)}`);
  }

  /** Sends a test message to the person's devices; the answer says how many accepted it. */
  async test() {
    return await this.requests.post<{ sent: number }>(`${prefix}/test`, {}, OWN_ERRORS);
  }
}
