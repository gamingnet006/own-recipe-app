// KH: the add-ons route guard runs before any component exists, so it must not reach for useI18n(), which throws
// outside a setup (vue-i18n error 26) and broke every page of the built app. It takes the app's own i18n instead.
import { beforeEach, describe, expect, test, vi } from "vitest";

const useRequests = vi.hoisted(() => vi.fn(() => ({})));
const useGlobalI18n = vi.hoisted(() => vi.fn(() => {
  throw new Error("26");
}));
const appI18n = vi.hoisted(() => ({ t: (key: string) => key, locale: { value: "de-DE" } }));
const navigateTo = vi.hoisted(() => vi.fn((to: string) => to));
const warning = vi.hoisted(() => vi.fn());

vi.mock("~/composables/api/api-client", () => ({ useRequests }));
vi.mock("~/composables/use-global-i18n", () => ({ useGlobalI18n }));
vi.mock("~/composables/use-toast", () => ({ alert: { warning, error: vi.fn() } }));
vi.mock("../lib/api/addons", () => ({
  KhAddonsApi: class {
    get() {
      const off = { shopping: false };
      return Promise.resolve({ data: { flags: off, enabled: off, unavailable: [] } });
    }
  },
}));

vi.stubGlobal("defineNuxtRouteMiddleware", (fn: unknown) => fn);
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { id: "u1", groupSlug: "home" } } }));
vi.stubGlobal("useNuxtApp", () => ({ $i18n: appI18n }));
vi.stubGlobal("navigateTo", navigateTo);
vi.stubGlobal("useGlobalI18n", useGlobalI18n);

describe("add-ons route guard", () => {
  beforeEach(() => {
    useRequests.mockClear();
    useGlobalI18n.mockClear();
  });

  test("loads the switches with the app's i18n and never calls useI18n outside a component", async () => {
    const { default: guard } = await import("../middleware/kh-addons.global");
    const result = await (guard as (to: { path: string }) => Promise<unknown>)({ path: "/shopping-lists" });
    expect(useRequests).toHaveBeenCalledWith(appI18n);
    expect(useGlobalI18n).not.toHaveBeenCalled();
    expect(result).toBe("/g/home");
    expect(warning).toHaveBeenCalled();
  });
});
