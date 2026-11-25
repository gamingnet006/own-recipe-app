// KH: tests for the own side menu's shared state (D58): loaded once per user, a failed load shows everything and is not
// retried at once, a save is taken over at once and keeps quick changes in order, a failed save brings the old list back,
// and the route guard loads with the app's i18n and forgets everything when nobody is signed in.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { khSidebar, loadKhSidebarFor, resetKhSidebar, saveKhLocale, saveKhSidebar, saveKhSimple } from "../composables/use-kh-sidebar";

const get = vi.hoisted(() => vi.fn());
const put = vi.hoisted(() => vi.fn());
const error = vi.hoisted(() => vi.fn());
const useRequests = vi.hoisted(() => vi.fn(() => ({})));
const user = vi.hoisted(() => ({ value: null as { id: string } | null }));
const appI18n = { t: (key: string) => key };

const applyKhLocale = vi.hoisted(() => vi.fn());
vi.mock("../composables/use-kh-locale", () => ({ applyKhLocale }));
vi.mock("../lib/api/navigation", () => ({ KhNavigationApi: class { get = get; put = put; } }));
vi.mock("~/composables/api/api-client", () => ({ useRequests }));
vi.mock("~/composables/use-global-i18n", () => ({ useGlobalI18n: () => ({ t: (key: string) => key }) }));
vi.mock("~/composables/use-toast", () => ({ alert: { error } }));
vi.stubGlobal("defineNuxtRouteMiddleware", (fn: unknown) => fn);
vi.stubGlobal("useMealieAuth", () => ({ user }));
vi.stubGlobal("useNuxtApp", () => ({ $i18n: appI18n }));

beforeEach(() => {
  get.mockReset();
  put.mockReset();
  error.mockReset();
  useRequests.mockClear();
  user.value = null;
  applyKhLocale.mockReset();
  resetKhSidebar();
});

describe("loadKhSidebarFor", () => {
  test("loads once per user and again for another one", async () => {
    get.mockResolvedValue({ data: { hidden: ["finder"] } });
    await loadKhSidebarFor("u1");
    await loadKhSidebarFor("u1");
    expect(get).toHaveBeenCalledTimes(1);
    expect(khSidebar.hidden).toEqual(["finder"]);
    get.mockResolvedValue({ data: { hidden: [] } });
    await loadKhSidebarFor("u2");
    expect(khSidebar.hidden).toEqual([]);
  });

  test("a failed load shows everything and is not asked again on every navigation", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    get.mockResolvedValue({ data: null });
    await loadKhSidebarFor("u1");
    await loadKhSidebarFor("u1");
    expect(khSidebar.hidden).toEqual([]);
    expect(get).toHaveBeenCalledTimes(1);
    resetKhSidebar();
    await loadKhSidebarFor("u1");
    expect(get).toHaveBeenCalledTimes(2);
  });
});

describe("saveKhSidebar", () => {
  test("shows the new list at once and takes the server's answer over", async () => {
    put.mockResolvedValue({ data: { hidden: ["finder", "timeline"] } });
    const saved = saveKhSidebar(["timeline", "finder"]);
    expect(khSidebar.hidden).toEqual(["timeline", "finder"]);
    await saved;
    expect(put).toHaveBeenCalledWith(["timeline", "finder"]);
    expect(khSidebar.hidden).toEqual(["finder", "timeline"]);
  });

  test("two quick changes both stay, and reach the server in order", async () => {
    put.mockImplementation(async (hidden: string[]) => ({ data: { hidden } }));
    const first = saveKhSidebar(["finder"]);
    const second = saveKhSidebar([...khSidebar.hidden, "timeline"]);
    await Promise.all([first, second]);
    expect(put.mock.calls.map(call => call[0])).toEqual([["finder"], ["finder", "timeline"]]);
    expect(khSidebar.hidden).toEqual(["finder", "timeline"]);
  });

  test("a failed save brings the old list back and tells the person", async () => {
    khSidebar.hidden = ["finder"];
    put.mockResolvedValue({ data: null });
    await saveKhSidebar(["finder", "timeline"]);
    expect(khSidebar.hidden).toEqual(["finder"]);
    expect(error).toHaveBeenCalled();
  });
});

describe("saveKhSimple", () => {
  test("shows the switch at once and stores it with the current list", async () => {
    khSidebar.hidden = ["finder"];
    put.mockResolvedValue({ data: { hidden: ["finder"], simple: true } });
    const saved = saveKhSimple(true);
    expect(khSidebar.simple).toBe(true);
    await saved;
    expect(put).toHaveBeenCalledWith(["finder"], true);
  });

  test("a failed save switches back and tells the person", async () => {
    put.mockResolvedValue({ data: null });
    await saveKhSimple(true);
    expect(khSidebar.simple).toBe(false);
    expect(error).toHaveBeenCalled();
  });

  test("is loaded with the list", async () => {
    get.mockResolvedValue({ data: { hidden: [], simple: true } });
    await loadKhSidebarFor("u1");
    expect(khSidebar.simple).toBe(true);
  });
});

describe("route guard", () => {
  test("loads with the app's i18n, never useI18n()", async () => {
    get.mockResolvedValue({ data: { hidden: ["cookbooks"] } });
    user.value = { id: "u1" };
    const { default: guard } = await import("../middleware/kh-sidebar.global");
    await (guard as () => Promise<unknown>)();
    expect(useRequests).toHaveBeenCalledWith(appI18n);
    expect(khSidebar.hidden).toEqual(["cookbooks"]);
  });

  test("shows the chosen language once per user, not on every navigation", async () => {
    get.mockResolvedValue({ data: { hidden: [], locale: "en-US" } });
    user.value = { id: "locale-user" };
    const { default: guard } = await import("../middleware/kh-sidebar.global");
    await (guard as () => Promise<unknown>)();
    await (guard as () => Promise<unknown>)();
    expect(applyKhLocale).toHaveBeenCalledTimes(1);
    expect(applyKhLocale).toHaveBeenCalledWith("en-US", appI18n);
  });

  test("a failed load applies no language; the retry that succeeds does", async () => {
    vi.useFakeTimers();
    vi.spyOn(console, "error").mockImplementation(() => {});
    get.mockResolvedValue({ data: null });
    user.value = { id: "retry-user" };
    const { default: guard } = await import("../middleware/kh-sidebar.global");
    await (guard as () => Promise<unknown>)();
    expect(applyKhLocale).not.toHaveBeenCalled();
    vi.advanceTimersByTime(61_000);
    get.mockResolvedValue({ data: { hidden: [], locale: "en-US" } });
    await (guard as () => Promise<unknown>)();
    expect(applyKhLocale).toHaveBeenCalledWith("en-US", appI18n);
    vi.useRealTimers();
  });

  test("forgets the list when nobody is signed in", async () => {
    khSidebar.hidden = ["cookbooks"];
    khSidebar.userId = "u1";
    const { default: guard } = await import("../middleware/kh-sidebar.global");
    await (guard as () => Promise<unknown>)();
    expect(khSidebar.hidden).toEqual([]);
    expect(khSidebar.userId).toBeNull();
    expect(get).not.toHaveBeenCalled();
  });
});

describe("language", () => {
  test("a load takes over the chosen language, an unknown or missing one is none", async () => {
    get.mockResolvedValue({ data: { hidden: [], simple: false, locale: "de-DE" } });
    await loadKhSidebarFor("u1");
    expect(khSidebar.locale).toBe("de-DE");
    get.mockResolvedValue({ data: { hidden: [], simple: false, locale: "fr-FR" } });
    await loadKhSidebarFor("u2");
    expect(khSidebar.locale).toBeNull();
  });

  test("a save stores the language with the current list and keeps the switch", async () => {
    khSidebar.hidden = ["finder"];
    put.mockResolvedValue({ data: { hidden: ["finder"], simple: false, locale: "en-US" } });
    await saveKhLocale("en-US");
    expect(put).toHaveBeenCalledWith(["finder"], undefined, "en-US");
    expect(khSidebar.locale).toBe("en-US");
  });

  test("a failed save is reported and the old choice returns", async () => {
    khSidebar.locale = "de-DE";
    put.mockResolvedValue({ data: null });
    await saveKhLocale("en-US");
    expect(error).toHaveBeenCalled();
    expect(khSidebar.locale).toBe("de-DE");
  });
});
