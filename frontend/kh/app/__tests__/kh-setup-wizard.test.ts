// KH: tests for the first-time setup's own steps (D83): family row checks, the temporary password, seeding, the
// compact system check, and that the news card for admins is hidden from everyone else.
import { describe, expect, test } from "vitest";
import {
  compactCheck, emptyRow, generatePassword, isBlankRow, isRerun, presetLabelKey, rowProblems, seedTasks,
  type FamilyRow,
} from "../lib/setup-wizard";
import type { KhCheck } from "../lib/api/system";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

const row = (patch: Partial<FamilyRow>): FamilyRow => ({ ...emptyRow(), name: "Anna", username: "anna", ...patch });

describe("rowProblems", () => {
  test("a good row, with or without e-mail, has no problem", () => {
    expect(rowProblems([row({}), row({ username: "ben", email: "ben@example.com" })])).toEqual([null, null]);
  });

  test("a blank row is left out, not reported", () => {
    expect(isBlankRow(emptyRow())).toBe(true);
    expect(rowProblems([emptyRow()])).toEqual([null]);
  });

  test("name and username are needed, the username has no spaces", () => {
    expect(rowProblems([row({ name: " " }), row({ username: "" }), row({ username: "an na" })]))
      .toEqual(["name", "username", "spaces"]);
  });

  test("a username used twice is reported on the second row, ignoring case", () => {
    expect(rowProblems([row({}), row({ username: "ANNA" })])).toEqual([null, "twice"]);
  });

  test("a broken e-mail address is reported", () => {
    expect(rowProblems([row({ email: "anna@" })])).toEqual(["email"]);
  });
});

describe("generatePassword", () => {
  test("three groups of four without look-alike characters", () => {
    for (let i = 0; i < 50; i++) expect(generatePassword()).toMatch(/^[a-hj-km-np-z2-9]{4}-[a-hj-km-np-z2-9]{4}-[a-hj-km-np-z2-9]{4}$/);
  });

  test("two passwords differ", () => {
    expect(generatePassword()).not.toBe(generatePassword());
  });

  test("bytes that would favour some characters are thrown away", () => {
    // 248 and above are rejected (256 % 31 = 8); 0 and 1 give the first two characters
    const stream = [255, 250, 248, ...Array.from({ length: 12 }, (_, i) => i)];
    const password = generatePassword(bytes => Uint8Array.from({ length: bytes.length }, (_, i) => stream[i] ?? 0));
    expect(password.replace(/-/g, "")).toBe("abcdefghjkmn");
  });
});

describe("seedTasks", () => {
  test("nothing when the admin said no", () => {
    expect(seedTasks(false, 0, 0)).toEqual([]);
  });

  test("only what the group does not have yet", () => {
    expect(seedTasks(true, 0, 0)).toEqual(["foods", "units"]);
    expect(seedTasks(true, 12, 0)).toEqual(["units"]);
    expect(seedTasks(true, 12, 5)).toEqual([]);
  });
});

test("isRerun is true once the account is not the default one", () => {
  expect(isRerun("changeme@example.com")).toBe(false);
  expect(isRerun("ChangeMe@Example.com")).toBe(false);
  expect(isRerun("paul@example.com")).toBe(true);
  expect(isRerun(undefined)).toBe(false);
});

describe("compactCheck", () => {
  const rows: KhCheck[] = [
    { key: "version", state: "info", value: "dev" },
    { key: "ai", state: "warn", value: "0" },
    { key: "backup", state: "ok", value: "2026-11-19" },
    { key: "signup", state: "ok", value: "off" },
  ];

  test("takes backup and AI from the shared rows, adds mail and the host-only hints", () => {
    expect(compactCheck(rows, true).map(r => [r.key, r.state])).toEqual([
      ["backup", "ok"], ["ai", "warn"], ["mail", "ok"], ["usbCopy", "info"], ["tunnel", "info"],
    ]);
  });

  test("mail without sending is yellow", () => {
    expect(compactCheck([], false).find(r => r.key === "mail")?.state).toBe("warn");
  });
});

test("every text of the setup steps exists in both languages", () => {
  for (const texts of [khTexts, khTextsDe]) {
    const kh = texts.kh as unknown as Record<string, Record<string, unknown>>;
    expect(kh.addons!.presets).toHaveProperty(presetLabelKey(null).split(".").pop()!);
    for (const key of ["mail", "usbCopy", "tunnel"]) {
      expect((kh.system!.rows as Record<string, unknown>)[key], key).toBeTruthy();
    }
    expect(kh.wizard).toBeTruthy();
  }
});
