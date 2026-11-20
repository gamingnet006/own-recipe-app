// KH: tests for the setup page's rules (D68): device detection, the sections per device, the stored ticks and answers,
// and when a new device is asked; every step has its text in both languages.
import { describe, expect, test } from "vitest";
import { DEFAULT_ADDONS } from "../lib/addons";
import {
  allStepKeys,
  ASK_AGAIN_DAYS,
  canInstallHere,
  canWriteNfc,
  detectDevice,
  isInstalled,
  keyName,
  parseAnswer,
  PRINT_QR_CLASS,
  printQrSheet,
  shoppingUrl,
  parseDone,
  asksForAddressAndKey,
  setupSections,
  shouldAskDevice,
  withDone,
} from "../lib/device-setup";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

const IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
const IPAD_AS_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15";
const ANDROID = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36";
const WINDOWS_EDGE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36 Edg/130.0";
const FIREFOX = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0";

describe("detectDevice", () => {
  test("knows iPhone, iPad, Android, Mac and other computers", () => {
    expect(detectDevice(IPHONE, 5)).toBe("iphone");
    expect(detectDevice("Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X)", 5)).toBe("ipad");
    expect(detectDevice(ANDROID, 5)).toBe("android");
    expect(detectDevice(IPAD_AS_MAC, 0)).toBe("mac");
    expect(detectDevice(WINDOWS_EDGE, 0)).toBe("computer");
  });

  test("a Mac that reports a touch screen is an iPad (iPadOS Safari names itself Macintosh)", () => {
    expect(detectDevice(IPAD_AS_MAC, 5)).toBe("ipad");
  });
});

describe("setupSections", () => {
  const ids = (device: Parameters<typeof setupSections>[0], on = DEFAULT_ADDONS) => setupSections(device, on).map(s => s.id);

  test("iPhone and iPad get everything", () => {
    expect(ids("iphone")).toEqual(["home", "list", "kitchen", "key", "import", "siri", "timer"]);
    expect(ids("ipad")).toEqual(ids("iphone"));
  });

  test("Android has no Siri and no Clock timer, Mac no timer, computers only install and key", () => {
    expect(ids("android")).toEqual(["home", "list", "kitchen", "key", "import"]);
    expect(ids("mac")).toEqual(["home", "list", "kitchen", "key", "import", "siri"]);
    expect(ids("computer")).toEqual(["home", "list", "kitchen", "key"]);
  });

  test("leaves out sections of switched-off add-ons", () => {
    expect(ids("iphone", { ...DEFAULT_ADDONS, shopping: false })).toEqual(["home", "key", "import", "timer"]);
    expect(ids("iphone", { ...DEFAULT_ADDONS, clock: false })).not.toContain("timer");
  });
});

test("the kitchen code points to the shopping list, and only Chrome on Android writes NFC (D81)", () => {
  expect(shoppingUrl("https://kochheft.example")).toBe("https://kochheft.example/einkauf");
  expect(canWriteNfc({ NDEFReader: () => undefined })).toBe(true);
  expect(canWriteNfc({})).toBe(false);
});

test("the QR print style is on only while printing (D81)", () => {
  const root = document.createElement("html");
  const listeners: Record<string, () => void> = {};
  const win = {
    print: () => expect(root.classList.contains(PRINT_QR_CLASS)).toBe(true),
    addEventListener: (name: string, fn: () => void) => { listeners[name] = fn; },
  };
  printQrSheet(root, win as unknown as Window);
  expect(root.classList.contains(PRINT_QR_CLASS)).toBe(true);
  listeners.afterprint!();
  expect(root.classList.contains(PRINT_QR_CLASS)).toBe(false);
});

test("every step and every section title has its text in both languages", () => {
  const paths = allStepKeys().flatMap(step => [step, step.replace(/\.s\d+$/, ".title")]);
  for (const texts of [khTexts, khTextsDe]) {
    for (const path of paths) {
      const text = path.split(".").reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], texts.kh.setup);
      expect(text, path).toBeTruthy();
    }
  }
});

describe("ticks", () => {
  test("round trip, and broken storage counts as nothing ticked", () => {
    expect(parseDone(JSON.stringify(withDone(withDone([], "home", true), "key", true)))).toEqual(["home", "key"]);
    expect(withDone(["home", "key"], "home", false)).toEqual(["key"]);
    expect(parseDone(null)).toEqual([]);
    expect(parseDone("not json")).toEqual([]);
    expect(parseDone("{\"a\":1}")).toEqual([]);
    expect(parseDone("[\"home\",\"bogus\",3]")).toEqual(["home"]);
  });
});

describe("shouldAskDevice", () => {
  const now = Date.UTC(2026, 10, 19);
  const day = 24 * 60 * 60 * 1000;

  test("asks on a phone or tablet that has not answered", () => {
    expect(shouldAskDevice(null, "iphone", IPHONE, now)).toBe(true);
    expect(shouldAskDevice(null, "android", ANDROID, now)).toBe(true);
  });

  test("never after \"never\"; again after a week after \"later\"", () => {
    expect(shouldAskDevice({ answer: "never", at: now - 100 * day }, "iphone", IPHONE, now)).toBe(false);
    expect(shouldAskDevice({ answer: "later", at: now - (ASK_AGAIN_DAYS - 1) * day }, "iphone", IPHONE, now)).toBe(false);
    expect(shouldAskDevice({ answer: "later", at: now - ASK_AGAIN_DAYS * day }, "iphone", IPHONE, now)).toBe(true);
  });

  test("\"yes\" is final too, so the question does not come back at every visit", () => {
    expect(shouldAskDevice({ answer: "yes", at: now - 100 * day }, "iphone", IPHONE, now)).toBe(false);
    expect(parseAnswer("{\"answer\":\"yes\",\"at\":5}")).toEqual({ answer: "yes", at: 5 });
  });

  test("computers are asked only in Safari, Chrome and Edge", () => {
    expect(shouldAskDevice(null, "mac", IPAD_AS_MAC, now)).toBe(true);
    expect(shouldAskDevice(null, "computer", WINDOWS_EDGE, now)).toBe(true);
    expect(shouldAskDevice(null, "computer", FIREFOX, now)).toBe(false);
    expect(canInstallHere(FIREFOX)).toBe(false);
  });

  test("parseAnswer takes only well-formed answers", () => {
    expect(parseAnswer("{\"answer\":\"later\",\"at\":5}")).toEqual({ answer: "later", at: 5 });
    expect(parseAnswer("{\"answer\":\"maybe\",\"at\":5}")).toBeNull();
    expect(parseAnswer("{\"answer\":\"later\"}")).toBeNull();
    expect(parseAnswer("x")).toBeNull();
    expect(parseAnswer(null)).toBeNull();
  });
});

test("isInstalled is true for either way of running as an app", () => {
  expect(isInstalled(true, undefined)).toBe(true);
  expect(isInstalled(false, true)).toBe(true);
  expect(isInstalled(false, undefined)).toBe(false);
});

test("keyName names the device and the day", () => {
  expect(keyName("iphone", new Date("2026-11-19T10:00:00Z"))).toBe("Kurzbefehle iPhone 2026-11-19");
  expect(keyName("iphone", new Date("2026-11-19T10:00:00Z"), 1)).toBe("Kurzbefehle iPhone 2026-11-19");
});

test("keyName tells further keys of the same day apart", () => {
  expect(keyName("mac", new Date("2026-11-19T10:00:00Z"), 2)).toBe("Kurzbefehle Mac 2026-11-19 (2)");
});

describe("asksForAddressAndKey", () => {
  it("is true for import and Siri on Apple devices, never on Android or other sections", () => {
    expect(asksForAddressAndKey("import", "ios")).toBe(true);
    expect(asksForAddressAndKey("siri", "mac")).toBe(true);
    expect(asksForAddressAndKey("import", "android")).toBe(false);
    expect(asksForAddressAndKey("key", "ios")).toBe(false);
  });
});
