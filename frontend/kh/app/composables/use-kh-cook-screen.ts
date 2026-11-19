// KH: cook mode gets the whole screen (D76): while "cook=true" is in the address, the layout hides the bar at the
// bottom, the side menu and the sign-out button, which cooking hands never need.
export function isCookScreen(query: Record<string, unknown>): boolean {
  return query.cook === "true";
}

/** True while the current page is the recipe page in cook mode. */
export function useKhCookScreen(): ComputedRef<boolean> {
  const route = useRoute();
  return computed(() => isCookScreen(route.query));
}
