// KH: tests for switching households (D52): the switch sets the new token and reloads the page, and the More entry
// exists only when the person has linked accounts.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { khAccounts, useKhAccounts } from "../composables/use-kh-accounts";
import { settingsTargets } from "../composables/use-kh-navigation";

const getMock = vi.hoisted(() => vi.fn());
const postMock = vi.hoisted(() => vi.fn());
const setToken = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, post: postMock }) }));
vi.mock("~/composables/use-auth-backend", () => ({ useAuthBackend: () => ({ setToken }) }));
const alertError = vi.hoisted(() => vi.fn());
vi.mock("~/composables/use-global-i18n", () => ({ useGlobalI18n: () => ({ t: (key: string) => key }) }));
vi.mock("~/composables/use-toast", () => ({ alert: { error: alertError } }));
vi.mock("~/composables/api", () => ({ useUserApi: () => ({}) }));
vi.mock("~/composables/use-logged-in-state", () => ({ useLoggedInState: () => ({ loggedIn: { value: true } }) }));

const account = (userId: string, group: string, current = false) => ({
  userId, fullName: "Anna", householdId: `h-${userId}`, household: `Haushalt ${userId}`, group, groupSlug: group, current,
});

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  setToken.mockReset();
  khAccounts.list = [];
  vi.stubGlobal("location", { assign: vi.fn() });
});

describe("switching", () => {
  test("load keeps the list of the server", async () => {
    getMock.mockResolvedValue({ data: [account("a", "familie", true), account("b", "oma")] });
    await useKhAccounts().load();
    expect(khAccounts.list.map(a => a.userId)).toEqual(["a", "b"]);
  });

  test("switchTo sets the new token and reloads in the target's group", async () => {
    getMock.mockResolvedValue({ data: [account("a", "familie", true), account("b", "oma")] });
    postMock.mockResolvedValue({ data: { access_token: "tok-b", token_type: "bearer" } });
    const { load, switchTo } = useKhAccounts();
    await load();
    await switchTo("b");
    expect(postMock).toHaveBeenCalledWith("/api/kh/accounts/switch", { userId: "b" });
    expect(setToken).toHaveBeenCalledWith("tok-b");
    expect(location.assign).toHaveBeenCalledWith("/g/oma");
  });

  test("a failed switch changes nothing", async () => {
    getMock.mockResolvedValue({ data: [account("a", "familie", true), account("b", "oma")] });
    postMock.mockResolvedValue({ data: null });
    const { load, switchTo } = useKhAccounts();
    await load();
    await switchTo("b");
    expect(setToken).not.toHaveBeenCalled();
    expect(location.assign).not.toHaveBeenCalled();
    expect(alertError).toHaveBeenCalled();
  });
});

describe("More entry", () => {
  test("shown only with linked accounts", () => {
    const keys = (linked: boolean) => settingsTargets({ admin: true, linked }, "familie").map(t => t.key);
    expect(keys(false)).not.toContain("switch");
    expect(keys(true)).toContain("switch");
  });

  test("the admin page is for admins only", () => {
    expect(settingsTargets({ admin: true }, "familie").map(t => t.key)).toContain("households");
    expect(settingsTargets({ admin: false }, "familie").map(t => t.key)).not.toContain("households");
  });
});
