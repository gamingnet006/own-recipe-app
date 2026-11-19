// KH: what another app's share sheet hands to the intake (D57): a link (recipe_import_url, Mealie's own share
// target) or a text (recipe_import_text), read from the page's query.

export interface SharedImport {
  link: string;
  text: string;
}

/** The first value of a query parameter, empty when there is none. */
function firstValue(value: unknown): string {
  const first = Array.isArray(value) ? value[0] : value;
  return typeof first === "string" ? first : "";
}

/** Whether the text is nothing but one http(s) address. */
function isWebAddress(text: string): boolean {
  try {
    return ["http:", "https:"].includes(new URL(text).protocol);
  }
  catch {
    return false;
  }
}

/** Reads the shared link and text from the query; a text longer than a draft takes is cut at maxText. Many apps
 * hand a link over as the share sheet's text (Mealie's manifest maps it to recipe_import_text), so a text that is
 * just an address becomes the link. */
export function readSharedImport(query: Record<string, unknown>, maxText: number): SharedImport {
  const link = firstValue(query.recipe_import_url);
  const text = firstValue(query.recipe_import_text);
  if (!link && isWebAddress(text.trim())) return { link: text.trim(), text: "" };
  return { link, text: text.slice(0, maxText) };
}

/** Whether the query still carries a shared link or text, so the page clears it once it has been taken over. */
export function hasSharedImport(query: Record<string, unknown>): boolean {
  return "recipe_import_url" in query || "recipe_import_text" in query;
}
