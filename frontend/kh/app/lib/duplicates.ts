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

/** Starts numbering requests: calling the result begins a request and returns a check that stays true only while no
 * newer request has begun, so an older answer arriving late can be ignored. */
export function latestRequest(): () => () => boolean {
  let newest = 0;
  return () => {
    const mine = ++newest;
    return () => mine === newest;
  };
}

/** The message for a recipe that could not be deleted: 403 means somebody else created it. */
export function deleteFailureKey(status: number | undefined): string {
  return status === 403 ? "kh.duplicates.delete-forbidden" : "kh.duplicates.failed";
}
