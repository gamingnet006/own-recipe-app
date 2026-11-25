// KH: the three kinds of account (Familie, Verwaltung, Admin) as Mealie's user flags, in both directions, so the admin
// chooses one kind instead of six checkboxes. Creating categories, tags and tools needs canOrganize, so every kind has it.

export const FLAG_KEYS = ["admin", "advanced", "canInvite", "canManage", "canManageHousehold", "canOrganize"] as const;
export type KhFlagKey = typeof FLAG_KEYS[number];
export type KhAccountFlags = Record<KhFlagKey, boolean>;

export const ACCOUNT_KINDS = ["family", "manager", "admin"] as const;
export type KhAccountKind = typeof ACCOUNT_KINDS[number];

const FAMILY: KhAccountFlags = {
  admin: false, advanced: false, canInvite: false, canManage: false, canManageHousehold: false, canOrganize: true,
};

const FLAGS_OF_KIND: Record<KhAccountKind, KhAccountFlags> = {
  family: FAMILY,
  manager: { ...FAMILY, canInvite: true, canManageHousehold: true },
  admin: { admin: true, advanced: true, canInvite: true, canManage: true, canManageHousehold: true, canOrganize: true },
};

/** The user flags of a kind. */
export function flagsOfKind(kind: KhAccountKind): KhAccountFlags {
  return { ...FLAGS_OF_KIND[kind] };
}

/** Only the six flags of a user object (or any object that has them). */
export function pickFlags(user: KhAccountFlags): KhAccountFlags {
  return Object.fromEntries(FLAG_KEYS.map(key => [key, !!user[key]])) as KhAccountFlags;
}

/** The kind these flags amount to, or "custom" for any other mix (an account with its own selection). */
export function kindOfFlags(user: KhAccountFlags): KhAccountKind | "custom" {
  const flags = pickFlags(user);
  return ACCOUNT_KINDS.find(kind => FLAG_KEYS.every(key => FLAGS_OF_KIND[kind][key] === flags[key])) ?? "custom";
}

/** One flag changed by hand. Admin switches every flag with it: on gives all, off goes back to a family account. */
export function applyFlag(user: KhAccountFlags, key: KhFlagKey, value: boolean): KhAccountFlags {
  const flags = pickFlags(user);
  if (key === "admin") return flagsOfKind(value ? "admin" : "family");
  return { ...flags, [key]: value };
}
