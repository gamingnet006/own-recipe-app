// KH: tests for creating the family in the setup wizard (D83): what happens with a tour that fails, a taken username and
// a server error, which rows stay, and that a retry never creates a person twice.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { discardRows, khFamily, pendingCount, resetKhFamily, useKhSetupFamily } from "../composables/use-kh-setup-family";
import { emptyRow, welcomeAddress, type FamilyRow } from "../lib/setup-wizard";

const createOne = vi.hoisted(() => vi.fn());
const post = vi.hoisted(() => vi.fn());
const put = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api", () => ({ useAdminApi: () => ({ users: { createOne } }) }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ post, put }) }));
vi.stubGlobal("useMealieAuth", () => ({ user: { value: { group: "Home", household: "Family" } } }));

const person = (name: string, patch: Partial<FamilyRow> = {}): FamilyRow => ({ ...emptyRow(), name, username: name.toLowerCase(), ...patch });
const created = (id: string) => ({ response: { status: 201 }, data: { id }, error: null });
const failedWith = (status: number) => ({ response: { status }, data: null, error: { response: { status } } });

beforeEach(() => {
  createOne.mockReset();
  post.mockReset();
  put.mockReset();
  post.mockResolvedValue({ error: null });
  put.mockResolvedValue({ error: null });
  resetKhFamily();
});

describe("createAll", () => {
  test("keeps the failed rows with their reason, reports the failed tour, and a retry skips the first person", async () => {
    khFamily.rows = [person("Anna"), person("Berta"), person("Cora")];
    createOne.mockResolvedValueOnce(created("1")).mockResolvedValueOnce(failedWith(409)).mockResolvedValueOnce(failedWith(500));
    post.mockResolvedValueOnce({ error: new Error("tour") });
    const { createAll } = useKhSetupFamily();

    expect(await createAll()).toEqual([{ name: "Anna", failed: "tour" }]);
    expect(khFamily.created.map(p => p.username)).toEqual(["anna"]);
    expect(khFamily.created[0]!.password).toMatch(/^[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}$/);
    expect(khFamily.rows.map(r => r.name)).toEqual(["Berta", "Cora"]);
    expect(khFamily.failures).toEqual({ 0: "taken", 1: "failed" });

    createOne.mockResolvedValue(created("2"));
    expect(await createAll()).toEqual([]);
    expect(createOne.mock.calls.map(call => call[0].username)).toEqual(["anna", "berta", "cora", "berta", "cora"]);
    expect(khFamily.created.map(p => p.username)).toEqual(["anna", "berta", "cora"]);
    expect(khFamily.rows).toEqual([emptyRow()]);
  });

  test("a failed simple view names the person and the simple view, not the tour", async () => {
    khFamily.rows = [person("Ben", { simple: true, tour: false })];
    createOne.mockResolvedValueOnce(created("3"));
    put.mockResolvedValueOnce({ error: new Error("simple") });
    expect(await useKhSetupFamily().createAll()).toEqual([{ name: "Ben", failed: "simple" }]);
    expect(post).not.toHaveBeenCalled();
  });

  test("the account kind sets the user flags, family being the default", async () => {
    khFamily.rows = [person("Anna"), person("Berta", { kind: "manager" })];
    createOne.mockResolvedValue(created("1"));
    await useKhSetupFamily().createAll();
    expect(createOne.mock.calls[0]![0]).toMatchObject({ admin: false, canOrganize: true, canInvite: false });
    expect(createOne.mock.calls[1]![0]).toMatchObject({ admin: false, canOrganize: true, canInvite: true, canManageHousehold: true });
  });

  test("a person's intolerances are stored for them, and a failure names the person", async () => {
    khFamily.rows = [person("Cora", { intolerances: ["milk"] }), person("Dora")];
    createOne.mockResolvedValue(created("7"));
    put.mockResolvedValueOnce({ error: new Error("x") });
    expect(await useKhSetupFamily().createAll()).toEqual([{ name: "Cora", failed: "intolerances" }]);
    expect(put).toHaveBeenCalledTimes(1); // Dora has no intolerances: nothing is stored, she is asked at her first sign-in
    expect(put).toHaveBeenCalledWith("/api/kh/admin/onboarding/7/intolerances", { allergens: ["milk"] }, expect.anything());
  });

  test("blank rows are ignored", async () => {
    khFamily.rows = [emptyRow(), person("Anna", { tour: false })];
    createOne.mockResolvedValueOnce(created("1"));
    await useKhSetupFamily().createAll();
    expect(createOne).toHaveBeenCalledTimes(1);
  });
});

test("editing a row clears what the server said about it", () => {
  khFamily.failures = { 0: "taken", 1: "failed" };
  useKhSetupFamily().clearFailure(0);
  expect(khFamily.failures).toEqual({ 1: "failed" });
});

test("pending rows are counted and can be discarded", () => {
  khFamily.rows = [person("Anna"), emptyRow(), person("Berta")];
  expect(pendingCount()).toBe(2);
  discardRows();
  expect(pendingCount()).toBe(0);
});

test("the welcome address is the configured base URL, else the page's address", () => {
  expect(welcomeAddress("https://kochen.example.com/", "http://localhost:9091")).toBe("https://kochen.example.com");
  expect(welcomeAddress(null, "http://localhost:9091")).toBe("http://localhost:9091");
});
