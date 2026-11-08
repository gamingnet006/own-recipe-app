// KH: the API of the family cookbook (D43) as a Mealie API class: print settings per cookbook, the own-photo flag
// of a recipe and the duplicate report. The types are written by hand like the notices' (mealie/kh/books, mealie/kh/duplicates).
import { BaseAPI } from "~/lib/api/base/base-clients";

const base = "/api/kh";

/** What one recipe contributes to a book. */
export interface KhBookRecipeSettings {
  include: boolean;
  photo: boolean;
  /** Null: the recipe's own number of servings. */
  servings: number | null;
}

export interface KhBookSettings {
  title: string | null;
  subtitle: string | null;
  titlePage: boolean;
  toc: boolean;
  order: "category" | "alpha";
  description: boolean;
  notes: boolean;
  oven: boolean;
  /** Keyed by recipe slug; a recipe without an entry has the defaults. */
  recipes: Record<string, KhBookRecipeSettings>;
}

export interface KhRecipeFlags {
  ownPhoto: boolean;
}

export type KhDuplicateKind = "duplicate_link" | "similar_title" | "similar_ingredients";

export interface KhRecipeRef {
  slug: string;
  name: string;
  orgUrl: string | null;
  tags: string[];
}

export interface KhDuplicatePair {
  a: KhRecipeRef;
  b: KhRecipeRef;
  kind: KhDuplicateKind;
  /** 0 to 1 */
  similarity: number;
}

export class KhBooksApi extends BaseAPI {
  /** The cookbook's stored print settings, or the defaults (title and subtitle null) when none are stored. */
  async getPrint(cookbookId: string) {
    return await this.requests.get<KhBookSettings>(`${base}/cookbooks/${cookbookId}/print`);
  }

  /** Stores the settings; the answer is what the server kept (photos only for recipes flagged as own). */
  async putPrint(cookbookId: string, settings: KhBookSettings) {
    return await this.requests.put<KhBookSettings>(`${base}/cookbooks/${cookbookId}/print`, settings);
  }

  /** The own-photo flags of SLUGS; a slug the server does not know is left out. */
  // ponytail: all slugs go in the URL; about 450+ recipes would hit the 16 KiB header limit, switch to POST then.
  async getFlags(slugs: string[]) {
    return await this.requests.get<Record<string, KhRecipeFlags>>(`${base}/recipes/flags?slugs=${slugs.map(encodeURIComponent).join(",")}`);
  }

  async putFlags(slug: string, ownPhoto: boolean) {
    return await this.requests.put<KhRecipeFlags>(`${base}/recipes/${encodeURIComponent(slug)}/flags`, { ownPhoto });
  }

  /** Possible doubles of the whole household, most similar first, optionally only recipes with the tag TAGID. */
  async getDuplicates(tagId?: string) {
    return await this.requests.get<KhDuplicatePair[]>(`${base}/duplicates${tagId ? `?tag=${encodeURIComponent(tagId)}` : ""}`);
  }

  /** "Keep both": the pair does not come up again. */
  async ignoreDuplicate(a: string, b: string) {
    return await this.requests.post<undefined>(`${base}/duplicates/ignore`, { a, b });
  }
}
