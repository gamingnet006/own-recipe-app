// KH: tests for the own side menu's shared state (D58): loaded once per user, a failed load shows everything and is not
// retried at once, a save is taken over at once and keeps quick changes in order, a failed save brings the old list back,
// and the route guard loads with the app's i18n and forgets everything when nobody is signed in.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { khSidebar, loadKhSidebarFor, resetKhSidebar, saveKhSidebar } from "../composables/use-kh-sidebar";

const get = vi.hoisted(() => vi.fn());
const put = vi.hoisted(() => vi.fn());
const error = vi.hoisted(() => vi.fn());
const useRequests = vi.hoisted(() => vi.fn(() => ({})));
const user = vi.hoisted(() => ({ value: null as { id: string } | null }));
const appI18n = { t: (key: string) => key };

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

describe("route guard", () => {
  test("loads with the app's i18n, never useI18n()", async () => {
    get.mockResolvedValue({ data: { hidden: ["cookbooks"] } });
    user.value = { id: "u1" };
    const { default: guard } = await import("../middleware/kh-sidebar.global");
    await (guard as () => Promise<unknown>)();
    expect(useRequests).toHaveBeenCalledWith(appI18n);
    expect(khSidebar.hidden).toEqual(["cookbooks"]);
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
