// KH: the tag suggestions for recipes without tags (mealie/kh/tags/schemas.py); the types are written by hand.
import { BaseAPI } from "~/lib/api/base/base-clients";

/** A tag of the group as a recipe holds it. */
export interface KhTagRef {
  id: string;
  name: string;
  slug: string;
}

/** The tags proposed for one recipe that has none. */
export interface KhTagProposal {
  recipeId: string;
  slug: string;
  name: string;
  tags: KhTagRef[];
}

export interface KhTagSuggestions {
  proposals: KhTagProposal[];
  aiAvailable: boolean;
  withoutProposal: number;
}

export class KhTagsApi extends BaseAPI {
  /** Proposals for recipes without tags; with USEAI also the AI for a few recipes the rules had nothing for. */
  async suggest(useAi: boolean) {
    return await this.requests.post<KhTagSuggestions, { useAi: boolean }>("/api/kh/tags/suggest", { useAi });
  }

  /** Adds the confirmed tags (per recipe, by ID); answers how many recipes changed. */
  async apply(items: { recipeId: string; tagIds: string[] }[]) {
    return await this.requests.post<{ changed: number }, { items: typeof items }>("/api/kh/tags/apply", { items });
  }
}
