// KH: the three account kinds and Mealie's user flags map onto each other in both directions.
import { describe, expect, test } from "vitest";
import { ACCOUNT_KINDS, applyFlag, flagsOfKind, kindOfFlags, pickFlags } from "../lib/account-kind";

describe("account kinds", () => {
  test("a family account can organize (categories, tags) but has no admin rights", () => {
    expect(flagsOfKind("family")).toEqual({
      admin: false, advanced: false, canInvite: false, canManage: false, canManageHousehold: false, canOrganize: true,
    });
  });

  test("administration adds inviting and managing the household", () => {
    const flags = flagsOfKind("manager");
    expect(flags).toMatchObject({ admin: false, canInvite: true, canManageHousehold: true, canOrganize: true, canManage: false });
  });

  test("an admin has every flag", () => {
    expect(Object.values(flagsOfKind("admin")).every(Boolean)).toBe(true);
  });

  test("every kind is recognized again from its flags", () => {
    for (const kind of ACCOUNT_KINDS) expect(kindOfFlags(flagsOfKind(kind))).toBe(kind);
  });

  test("any other mix is a custom choice", () => {
    expect(kindOfFlags({ ...flagsOfKind("family"), advanced: true })).toBe("custom");
    expect(kindOfFlags({ ...flagsOfKind("family"), canOrganize: false })).toBe("custom");
  });

  test("a whole user object is read for its flags only", () => {
    expect(kindOfFlags({ ...flagsOfKind("manager"), username: "x", id: "1" } as never)).toBe("manager");
    expect(Object.keys(pickFlags({ ...flagsOfKind("family"), username: "x" } as never)).sort())
      .toEqual(["admin", "advanced", "canInvite", "canManage", "canManageHousehold", "canOrganize"]);
  });

  test("ticking admin ticks everything and unticking goes back to a family account, other flags change alone", () => {
    expect(applyFlag(flagsOfKind("family"), "admin", true)).toEqual(flagsOfKind("admin"));
    expect(applyFlag(flagsOfKind("admin"), "admin", false)).toEqual(flagsOfKind("family"));
    expect(applyFlag(flagsOfKind("family"), "canInvite", true).canInvite).toBe(true);
  });
});
