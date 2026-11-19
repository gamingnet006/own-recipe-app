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

// The last character is not sentence punctuation or a closing bracket: "(link)." gives the link alone (as the
// Telegram bot reads links).
const WEB_ADDRESS = /https?:\/\/\S*[^\s.,;:!?)»]/gi;

// Words around the link that still make a share message, not a recipe ("Schau mal: Grießpudding <link>").
const SHARE_MESSAGE_MAX = 200;

/** The one http(s) address a short share message carries; empty for a longer text or several addresses, which
 * stay a text (a recipe from Notes may name its source). */
function sharedAddress(text: string): string {
  const found = text.match(WEB_ADDRESS) ?? [];
  if (found.length !== 1) return "";
  return text.replace(found[0], "").trim().length <= SHARE_MESSAGE_MAX ? found[0] : "";
}

/** Reads the shared link and text from the query; a text longer than a draft takes is cut at maxText. Many apps
 * hand a link over as the share sheet's text (Mealie's manifest maps it to recipe_import_text), often with a few
 * words around it (Chefkoch, Rezeptwelt), so a short message with one address becomes the link. */
export function readSharedImport(query: Record<string, unknown>, maxText: number): SharedImport {
  const link = firstValue(query.recipe_import_url);
  const text = firstValue(query.recipe_import_text);
  const address = link ? "" : sharedAddress(text);
  if (address) return { link: address, text: "" };
  return { link, text: text.slice(0, maxText) };
}

/** Whether the query still carries a shared link or text, so the page clears it once it has been taken over. */
export function hasSharedImport(query: Record<string, unknown>): boolean {
  return "recipe_import_url" in query || "recipe_import_text" in query;
}
