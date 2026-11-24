// KH: moving one photo of several one place earlier or later: the first photo is the recipe's cover, so people reorder.

/** The old positions (from 0) in their new order after moving INDEX one place by BY; null at the ends, where it cannot move. */
export function movedOrder(count: number, index: number, by: -1 | 1): number[] | null {
  const target = index + by;
  if (index < 0 || index >= count || target < 0 || target >= count) return null;
  const order = Array.from({ length: count }, (_, i) => i);
  [order[index], order[target]] = [target, index];
  return order;
}

/** The items in the given order of old positions. */
export function applyOrder<T>(items: T[], order: number[]): T[] {
  return order.map(position => items[position]!);
}
