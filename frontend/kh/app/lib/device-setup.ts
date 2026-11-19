// KH: the rules of the setup page "Kochheft einrichten" and of the question on a new device (D68), without any screen:
// which device this is, which sections it gets with how many steps, what was ticked off, and when to ask again.
import type { KhAddonFlags } from "./addons";

/** Where the setup page lives; the tour, the news, the question on a new device and Mehr open it. */
export const SETUP_PATH = "/aufs-handy";

export type KhDevice = "iphone" | "ipad" | "android" | "mac" | "computer";
/** Devices that share one set of texts: iPhone and iPad work alike. */
export type KhFamily = "ios" | "android" | "mac" | "computer";
export type KhSetupSection = "home" | "list" | "key" | "import" | "siri" | "timer";

export const DEVICES: KhDevice[] = ["iphone", "ipad", "android", "mac", "computer"];

/** The device from the browser's own name. iPadOS Safari names itself "Macintosh", so a Mac with a touch screen is
 * an iPad. Anything that is not iOS, Android or a Mac counts as a computer (Windows, Linux). */
export function detectDevice(userAgent: string, touchPoints: number): KhDevice {
  if (/iPhone|iPod/.test(userAgent)) return "iphone";
  if (/iPad/.test(userAgent) || (/Macintosh/.test(userAgent) && touchPoints > 1)) return "ipad";
  if (/Android/.test(userAgent)) return "android";
  return /Macintosh/.test(userAgent) ? "mac" : "computer";
}

export function familyOf(device: KhDevice): KhFamily {
  return device === "iphone" || device === "ipad" ? "ios" : device;
}

/** Whether the browser can install the app or put it in the Dock; Firefox cannot, so computers there are not asked. */
export function canInstallHere(userAgent: string): boolean {
  return /Safari\/|Chrome\/|Edg\//.test(userAgent) && !/Firefox\/|FxiOS|OPR\//.test(userAgent);
}

/** Steps per section and family (0: the section is not shown there). The texts are kh.setup.<section>.<family>.s<n>. */
const STEPS: Record<KhSetupSection, Partial<Record<KhFamily, number>>> = {
  home: { ios: 3, android: 3, mac: 3, computer: 3 },
  list: { ios: 4, android: 3, mac: 3, computer: 3 },
  key: { ios: 3, android: 3, mac: 3, computer: 3 },
  import: { ios: 3, mac: 3, android: 1 },
  siri: { ios: 3, mac: 2 },
  timer: { ios: 2 },
};

/** The add-on a section needs, if any: the list and Siri need the shopping list, the timer the Clock timer. */
const SECTION_ADDON: Partial<Record<KhSetupSection, keyof KhAddonFlags>> = { list: "shopping", siri: "shopping", timer: "clock" };

export interface KhSectionPlan {
  id: KhSetupSection;
  steps: number;
}

/** The sections this device gets, in order, with their number of steps; sections of switched-off add-ons are left out. */
export function setupSections(device: KhDevice, on: KhAddonFlags): KhSectionPlan[] {
  const family = familyOf(device);
  const plans: KhSectionPlan[] = [];
  for (const id of Object.keys(STEPS) as KhSetupSection[]) {
    const steps = STEPS[id][family];
    const addon = SECTION_ADDON[id];
    if (steps && (!addon || on[addon])) plans.push({ id, steps });
  }
  return plans;
}

/** Every (section, family, step count) pair, for checking that all texts exist. */
export function allStepKeys(): string[] {
  return (Object.keys(STEPS) as KhSetupSection[]).flatMap(id =>
    (Object.entries(STEPS[id]) as [KhFamily, number][]).flatMap(([family, count]) =>
      Array.from({ length: count }, (_, i) => `${id}.${family}.s${i + 1}`)));
}

/** Whether the app runs installed (home screen or Dock) and not in a browser tab. */
export function isInstalled(standaloneMedia: boolean, navigatorStandalone: boolean | undefined): boolean {
  return standaloneMedia || navigatorStandalone === true;
}

/** Name of the API key made on this device, e.g. "Kurzbefehle iPhone 2026-11-19". */
export function keyName(device: KhDevice, date: Date): string {
  const label = { iphone: "iPhone", ipad: "iPad", android: "Android", mac: "Mac", computer: "Computer" }[device];
  return `Kurzbefehle ${label} ${date.toISOString().slice(0, 10)}`;
}

/** The sections ticked off, from the stored text; anything broken counts as nothing ticked. */
export function parseDone(raw: string | null): KhSetupSection[] {
  try {
    const list = JSON.parse(raw ?? "[]") as unknown;
    return Array.isArray(list) ? list.filter((id): id is KhSetupSection => typeof id === "string" && id in STEPS) : [];
  }
  catch {
    return [];
  }
}

/** DONE with ID ticked or unticked. */
export function withDone(done: KhSetupSection[], id: KhSetupSection, ticked: boolean): KhSetupSection[] {
  const rest = done.filter(item => item !== id);
  return ticked ? [...rest, id] : rest;
}

export const ASK_AGAIN_DAYS = 7;
const DAY_MS = 24 * 60 * 60 * 1000;

export interface KhDeviceAnswer {
  answer: "later" | "never" | "yes";
  at: number;
}

/** The stored answer of the new-device question; null when there is none or it is broken. */
export function parseAnswer(raw: string | null): KhDeviceAnswer | null {
  try {
    const value = JSON.parse(raw ?? "null") as Partial<KhDeviceAnswer> | null;
    const known = value?.answer === "later" || value?.answer === "never" || value?.answer === "yes";
    return known && typeof value.at === "number" ? (value as KhDeviceAnswer) : null;
  }
  catch {
    return null;
  }
}

/** Whether to ask the person about setting this device up: never answered, or "later" at least a week ago ("yes" and
 * "never" are final: the person was shown the page or declined). Phones and
 * tablets always qualify; computers only in a browser that can install the app (Safari, Chrome, Edge). */
export function shouldAskDevice(answer: KhDeviceAnswer | null, device: KhDevice, userAgent: string, now: number): boolean {
  if ((device === "mac" || device === "computer") && !canInstallHere(userAgent)) return false;
  if (!answer) return true;
  return answer.answer === "later" && now - answer.at >= ASK_AGAIN_DAYS * DAY_MS;
}
