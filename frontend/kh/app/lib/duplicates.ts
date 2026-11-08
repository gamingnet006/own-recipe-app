// KH: the words for the duplicate report's cards (D43): how similar a pair is and where a recipe came from.
import type { KhDuplicatePair } from "./api/books";

type Translate = (key: string) => string;

/** "ähnlicher Titel · 85 %": the kind of match in words and the similarity in whole percent. */
export function pairLabel(pair: KhDuplicatePair, t: Translate): string {
  return `${t(`kh.duplicates.${pair.kind}`)} · ${Math.round(pair.similarity * 100)} %`;
}

/** The site a recipe was taken from ("example.com"), or null for one entered by hand or a link that is not a web address. */
export function originOf(orgUrl: string | null): string | null {
  try {
    return orgUrl ? new URL(orgUrl).hostname.replace(/^www\./, "") : null;
  }
  catch {
    return null;
  }
}
