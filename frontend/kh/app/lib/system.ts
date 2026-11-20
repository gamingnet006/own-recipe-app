// KH: words and links for the system check (P8.3): what a row says, which colour its light has, and the first-start list.
import type { KhCheck, KhLight } from "./api/system";

/** How a light looks: Vuetify colour and the name of one of Mealie's icons. */
export const LIGHTS: Record<KhLight, { color: string; icon: string }> = {
  ok: { color: "success", icon: "checkboxMarkedCircle" },
  warn: { color: "warning", icon: "alertCircle" },
  bad: { color: "error", icon: "alertCircle" },
  info: { color: "info", icon: "informationOutline" },
};

type Translate = (key: string, values?: Record<string, string>) => string;

/** The sentence of a row; on/off values, the backup without any file and a silent nightly update have their own words. */
export function rowText(t: Translate, row: KhCheck): string {
  const stale = row.key === "autoUpdate" && row.value === "stale";
  const state = row.key === "backup" && !row.value ? "none" : stale ? "stale" : row.state;
  const value = row.value === "on" || row.value === "off" ? t(`kh.system.${row.value}`) : row.value;
  // the address row carries "<now> <before>" (D85)
  const [current = "", previous = ""] = row.key === "address" ? row.value.split(" ") : [];
  const text = t(`kh.system.rows.${row.key}.${state}`, { value, current, previous });
  return row.key === "autoUpdate" && value && !stale ? `${text} ${value}` : text;
}

export interface KhStartStep {
  key: string;
  to: string;
  external: boolean;
}

/** The first-start list: places inside the app, and the guide for what only the host's scripts do. */
export function firstStartSteps(sourceUrl: string): KhStartStep[] {
  const guide = (file: string) => `${sourceUrl}/blob/main/docs/kh/${file}`;
  return [
    { key: "ai", to: "/group", external: false },
    { key: "accounts", to: "/admin/manage/users", external: false },
    { key: "backup", to: "/admin/backups", external: false },
    { key: "tunnel", to: guide("README.md"), external: true },
    { key: "shortcut", to: guide("README.md"), external: true },
  ];
}
