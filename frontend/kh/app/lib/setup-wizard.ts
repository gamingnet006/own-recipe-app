// KH: the rules of the first-time setup's own steps (D83) without any screen: the family rows and their checks, the
// temporary password, the text for a new person, what to seed, and the compact system check.
import type { KhCheck } from "./api/system";
import type { KhPreset } from "./addons";
import type { KhAccountKind } from "./account-kind";
import type { KhAllergenKey } from "./api/allergens";

/** Where Mealie's setup wizard lives; the news card and Mehr → Einstellungen open it again. */
export const WIZARD_PATH = "/admin/setup";

/** Mealie's well-known first account; as long as the admin has it, the wizard is the first run. */
const DEFAULT_ACCOUNT_EMAIL = "changeme@example.com";

/** True when the wizard runs for an install that was set up before: the account is no longer the default one. */
export function isRerun(adminEmail: string | undefined): boolean {
  return !!adminEmail && adminEmail.toLowerCase() !== DEFAULT_ACCOUNT_EMAIL;
}

export interface FamilyRow {
  name: string;
  username: string;
  email: string;
  /** Show the first-sign-in tour (D59). */
  tour: boolean;
  /** Start with the simple view (D79). */
  simple: boolean;
  /** The kind of account (Familie by default). */
  kind: KhAccountKind;
  /** What this person does not tolerate (optional, only asked with the add-on Allergene). */
  intolerances: KhAllergenKey[];
}

export type RowProblem = "name" | "username" | "spaces" | "twice" | "email";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function emptyRow(): FamilyRow {
  return { name: "", username: "", email: "", tour: true, simple: false, kind: "family", intolerances: [] };
}

/** A row nobody typed into is left out instead of reported. */
export function isBlankRow(row: FamilyRow): boolean {
  return !row.name.trim() && !row.username.trim() && !row.email.trim();
}

/** What is wrong with each row (null: fine, also for blank rows). A username used by an earlier row counts as taken. */
export function rowProblems(rows: FamilyRow[]): (RowProblem | null)[] {
  const seen = new Set<string>();
  return rows.map((row) => {
    if (isBlankRow(row)) return null;
    const username = row.username.trim().toLowerCase();
    const problem: RowProblem | null = !row.name.trim()
      ? "name"
      : !username
          ? "username"
          : /\s/.test(username)
            ? "spaces"
            : seen.has(username)
              ? "twice"
              : row.email.trim() && !EMAIL_PATTERN.test(row.email.trim())
                ? "email"
                : null;
    seen.add(username);
    return problem;
  });
}

// 31 letters and digits without look-alikes (no i, l, o, 0, 1)
const PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789";
const PASSWORD_GROUPS = 3;
const PASSWORD_GROUP_LENGTH = 4;

/** A temporary password such as "k7pd-x3mw-ha4t", from the browser's random numbers (RANDOM is replaceable for tests).
 * Bytes that would favour some characters are thrown away. */
export function generatePassword(random: (bytes: Uint8Array) => Uint8Array = bytes => crypto.getRandomValues(bytes)): string {
  const limit = 256 - (256 % PASSWORD_ALPHABET.length);
  const chars: string[] = [];
  while (chars.length < PASSWORD_GROUPS * PASSWORD_GROUP_LENGTH) {
    for (const byte of random(new Uint8Array(32))) {
      if (byte < limit && chars.length < PASSWORD_GROUPS * PASSWORD_GROUP_LENGTH) chars.push(PASSWORD_ALPHABET[byte % PASSWORD_ALPHABET.length]!);
    }
  }
  const groups = Array.from({ length: PASSWORD_GROUPS }, (_, i) => chars.slice(i * PASSWORD_GROUP_LENGTH, (i + 1) * PASSWORD_GROUP_LENGTH).join(""));
  return groups.join("-");
}

/** The address to give a new person: Mealie's configured BASE_URL when it is set, else the address the admin is on. */
export function welcomeAddress(baseUrl: string | null, origin: string): string {
  return (baseUrl || origin).replace(/\/+$/, "");
}

/** Which of foods and units to seed: nothing when the admin said no, and not what the group already has (an install
 * that runs the wizard again keeps its own lists). */
export function seedTasks(useSeedData: boolean, foods: number, units: number): ("foods" | "units")[] {
  if (!useSeedData) return [];
  return [...(foods === 0 ? ["foods" as const] : []), ...(units === 0 ? ["units" as const] : [])];
}

/** The name of the preset the two big switches show, for the summary; "custom" for the mix. */
export function presetLabelKey(preset: KhPreset | null): string {
  return `kh.addons.presets.${preset ?? "custom"}`;
}

// The rows of the compact check: what Mealie's system check already reports, in the order the setup shows them
const CHECK_KEYS = ["backup", "autoUpdate", "ai"];

/** The compact system check: the shared rows for backup, automatic updates and AI, mail sending from the server's
 * flag, and the two things only the host's scripts know (USB copy, remote access) as hints. */
export function compactCheck(rows: KhCheck[], emailReady: boolean): KhCheck[] {
  const wanted = CHECK_KEYS.map(key => rows.find(row => row.key === key)).filter((row): row is KhCheck => !!row);
  return [
    ...wanted,
    { key: "mail", state: emailReady ? "ok" : "warn", value: "" },
    { key: "usbCopy", state: "info", value: "" },
    { key: "tunnel", state: "info", value: "" },
  ];
}
