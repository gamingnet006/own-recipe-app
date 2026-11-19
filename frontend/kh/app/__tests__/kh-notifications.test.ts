// KH: tests for the notifications page's rules (D75): what blocks a device, the key conversion, and that every event
// has its text in both languages.
import { describe, expect, test } from "vitest";
import { EVENTS, keyToBytes, pushBlocker, type KhPushEnv } from "../lib/notifications";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

const IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
const MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15";
const env = (over: Partial<KhPushEnv>): KhPushEnv => ({
  userAgent: MAC, touchPoints: 0, installed: false, apis: true, permission: "default", ...over,
});

describe("pushBlocker", () => {
  test("a computer browser with the APIs is free to go", () => {
    expect(pushBlocker(env({}))).toBeNull();
  });

  test("iPhone and iPad need the app on the home screen first, even when an API is missing", () => {
    expect(pushBlocker(env({ userAgent: IPHONE, touchPoints: 5, apis: false }))).toBe("install-first");
    expect(pushBlocker(env({ touchPoints: 5 }))).toBe("install-first"); // iPadOS names itself Macintosh
    expect(pushBlocker(env({ userAgent: IPHONE, touchPoints: 5, installed: true }))).toBeNull();
  });

  test("missing APIs and a refused permission are told apart", () => {
    expect(pushBlocker(env({ apis: false }))).toBe("unsupported");
    expect(pushBlocker(env({ permission: "denied" }))).toBe("denied");
  });
});

test("keyToBytes decodes URL-safe base64 with and without padding", () => {
  expect(Array.from(keyToBytes("AQID"))).toEqual([1, 2, 3]);
  expect(Array.from(keyToBytes("-_8"))).toEqual([251, 255]);
});

test("every event has a title and a text in both languages", () => {
  for (const texts of [khTexts, khTextsDe]) {
    const events = texts.kh.notifications.events as Record<string, { title: string; text: string }>;
    for (const event of EVENTS) {
      expect(events[event]?.title, event).toBeTruthy();
      expect(events[event]?.text, event).toBeTruthy();
    }
  }
});
