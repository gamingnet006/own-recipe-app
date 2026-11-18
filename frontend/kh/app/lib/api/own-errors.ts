// KH: request option for calls whose page shows its own error text (duplicates, "link expired"); without it Mealie's
// axios plugin adds a second, generic "request failed with status 409" toast since Mealie 3.31.
export const OWN_ERRORS = { suppressAlert: true } as const;
