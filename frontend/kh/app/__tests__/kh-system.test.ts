// KH: tests for the system check's words and links (P8.3) and that both languages word every row the backend can send.
import { describe, expect, test } from "vitest";
import { firstStartSteps, LIGHTS, rowText } from "../lib/system";
import type { KhCheck } from "../lib/api/system";
import { icons } from "~/lib/icons";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

/** A translator over one language's texts, filling {value} like vue-i18n. */
function translator(texts: object) {
  return (key: string, values: Record<string, string> = {}) => {
    const found = key.split(".").reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], texts);
    return String(found).replace(/\{(\w+)\}/g, (_, name: string) => values[name] ?? "");
  };
}
const en = translator(khTexts);

// Every key and state mealie/kh/system/checks.py can send
const STATES: Record<string, string[]> = {
  version: ["info"],
  database: ["info"],
  disk: ["ok", "warn", "bad"],
  backup: ["ok", "warn", "bad"],
  ai: ["ok", "warn"],
  signup: ["ok", "bad"],
  defaultAccount: ["ok", "bad"],
  autoUpdate: ["ok", "warn", "info", "bad"],
  nutrition: ["ok", "bad"],
  telegram: ["info"],
  whisper: ["info"],
};

describe("row texts", () => {
  test("a row says its value", () => {
    expect(rowText(en, { key: "disk", state: "warn", value: "1.5 GB" })).toBe("Little free space: 1.5 GB");
    expect(rowText(en, { key: "version", state: "info", value: "v0.5" })).toBe("Version: v0.5");
  });

  test("on and off are worded in the language", () => {
    expect(rowText(en, { key: "telegram", state: "info", value: "on" })).toBe("Telegram bot: on");
    expect(rowText(translator(khTextsDe), { key: "whisper", state: "info", value: "off" })).toBe(
      "Spracherkennung (Whisper): aus",
    );
  });

  test("a missing backup has its own sentence", () => {
    expect(rowText(en, { key: "backup", state: "bad", value: "" })).toBe("There is no backup yet.");
  });

  test("the last automatic run follows the sentence", () => {
    const row: KhCheck = { key: "autoUpdate", state: "ok", value: "2026-11-08 04:00 Aktuell" };
    expect(rowText(en, row)).toBe("Automatic updates are on. 2026-11-08 04:00 Aktuell");
    expect(rowText(en, { ...row, value: "" })).toBe("Automatic updates are on.");
  });

  test("both languages word every key and state", () => {
    for (const texts of [khTexts, khTextsDe]) {
      const t = translator(texts);
      for (const [key, states] of Object.entries(STATES)) {
        for (const state of states) {
          expect(rowText(t, { key, state: state as KhCheck["state"], value: "x" }), `${key}.${state}`).not.toContain("undefined");
        }
      }
      expect(t("kh.system.rows.backup.none")).not.toBe("undefined");
    }
  });
});

test("every light has one of Mealie's icons", () => {
  for (const light of Object.values(LIGHTS)) expect(icons).toHaveProperty(light.icon);
});

test("the first-start list links inside the app and to the guide", () => {
  const steps = firstStartSteps("https://example.org/own");
  expect(steps.map(step => step.key)).toEqual(["ai", "accounts", "backup", "tunnel", "shortcut"]);
  expect(steps.filter(step => !step.external).map(step => step.to)).toEqual(["/group", "/admin/manage/users", "/admin/backups"]);
  expect(steps.filter(step => step.external).every(step => step.to.startsWith("https://example.org/own/blob/main/docs/kh/")))
    .toBe(true);
  for (const texts of [khTexts, khTextsDe]) {
    for (const step of steps) expect(typeof (texts.kh.system.start as Record<string, string>)[step.key]).toBe("string");
  }
});
