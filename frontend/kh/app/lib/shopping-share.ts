// KH: the text of the shopping list as it is handed to another app's share sheet (D56).

/** The items still to buy, one per line and without label headings (another app would take a heading for an item). */
export function shareText(items: { display?: string | null; checked?: boolean | null }[]): string {
  return items
    .filter(item => !item.checked && item.display)
    .map(item => item.display)
    .join("\n");
}
