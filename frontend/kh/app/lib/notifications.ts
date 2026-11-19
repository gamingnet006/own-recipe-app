// KH: the rules of the notifications page (D75) without any screen: whether this device can get push messages, the
// events with their texts' keys, and the conversion of the server's public key for the browser.
import { familyOf, detectDevice } from "./device-setup";

export const EVENTS = ["plan", "evening", "shopping", "wishes", "intake", "news"] as const;
export type KhNotificationEvent = typeof EVENTS[number];

export type KhNotificationSettings = Record<KhNotificationEvent, boolean> & { eveningTime: string };

export type KhPushBlocker = "unsupported" | "install-first" | "denied" | null;

export interface KhPushEnv {
  userAgent: string;
  touchPoints: number;
  /** Runs installed (home screen or Dock), not in a browser tab. */
  installed: boolean;
  /** serviceWorker, PushManager and Notification all exist. */
  apis: boolean;
  /** Notification.permission; "default" while not asked. */
  permission: NotificationPermission;
}

/** What keeps this device from getting push messages, or null. iPhone and iPad (16.4 or newer) only deliver them to
 * an app on the home screen, so there the answer is "install first" until it is installed. */
export function pushBlocker(env: KhPushEnv): KhPushBlocker {
  const ios = familyOf(detectDevice(env.userAgent, env.touchPoints)) === "ios";
  if (ios && !env.installed) return "install-first";
  if (!env.apis) return "unsupported";
  return env.permission === "denied" ? "denied" : null;
}

/** The server's URL-safe base64 key as the bytes pushManager.subscribe wants. */
export function keyToBytes(key: string): Uint8Array<ArrayBuffer> {
  const padded = (key + "=".repeat((4 - (key.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(padded), char => char.charCodeAt(0));
}
