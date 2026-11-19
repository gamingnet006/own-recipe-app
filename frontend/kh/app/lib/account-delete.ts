// KH: the pure checks of deleting an account (D78): when the typed name confirms it, and who can take over the recipes.

/** True when TYPED is the username, ignoring case and surrounding spaces, as the server checks it. */
export function confirmMatches(typed: string, username: string): boolean {
  return username !== "" && typed.trim().toLowerCase() === username.toLowerCase();
}

/** The people who can inherit from the user TARGET_ID: the others of the same household. */
export function heirOptions<T extends { id: string; householdId: string }>(users: T[], targetId: string): T[] {
  const target = users.find(user => user.id === targetId);
  return target ? users.filter(user => user.id !== targetId && user.householdId === target.householdId) : [];
}
