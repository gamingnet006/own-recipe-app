// KH: the API of allergens (D44) as a Mealie API class: what a recipe probably contains and the corrections to it, the
// own intolerances, warnings for the cards, substitution rules and variants. Types by hand (mealie/kh/allergens).
import { BaseAPI } from "~/lib/api/base/base-clients";

const base = "/api/kh";

/** The 14 groups of Annex II of Regulation (EU) 1169/2011, with the fixed keys of the server. */
export const KH_ALLERGENS = [
  "gluten", "crustaceans", "eggs", "fish", "peanuts", "soy", "milk", "nuts", "celery", "mustard", "sesame", "sulphites",
  "lupin", "molluscs",
] as const;

export type KhAllergenKey = typeof KH_ALLERGENS[number];

export interface KhAllergenHit {
  allergen: KhAllergenKey;
  /** The ingredient lines the allergen was recognised from. */
  lines: string[];
  /** Null: as recognised; false: taken out by hand; true: added by hand. */
  corrected: boolean | null;
}

export interface KhAllergenWarning {
  allergen: KhAllergenKey;
  /** Full names of the household's members who do not tolerate it. */
  names: string[];
}

export interface KhSubstitutionHint {
  line: string;
  allergen: KhAllergenKey;
  replacement: string;
}

export interface KhRecipeAllergens {
  hits: KhAllergenHit[];
  warnings: KhAllergenWarning[];
  substitutions: KhSubstitutionHint[];
}

export interface KhSubstitutionRule {
  id: string;
  match: string;
  replacement: string;
  allergen: KhAllergenKey;
}

export class KhAllergensApi extends BaseAPI {
  async forRecipe(slug: string) {
    return await this.requests.get<KhRecipeAllergens>(`${base}/recipes/${encodeURIComponent(slug)}/allergens`);
  }

  /** PRESENT true adds the allergen, false takes a recognised one out, null removes the correction. */
  async correct(slug: string, allergen: KhAllergenKey, present: boolean | null) {
    return await this.requests.put<{ present: boolean | null }>(`${base}/recipes/${encodeURIComponent(slug)}/allergens/${allergen}`, { present });
  }

  async getAllergies() {
    return await this.requests.get<{ allergens: KhAllergenKey[] }>(`${base}/users/self/allergies`);
  }

  async putAllergies(allergens: KhAllergenKey[]) {
    return await this.requests.put<{ allergens: KhAllergenKey[] }>(`${base}/users/self/allergies`, { allergens });
  }

  /** Recipe slug to the allergens somebody in the household does not tolerate; recipes without a warning are left out. */
  async getWarnings() {
    return await this.requests.get<Record<string, KhAllergenKey[]>>(`${base}/allergens/warnings`);
  }

  async getRules() {
    return await this.requests.get<KhSubstitutionRule[]>(`${base}/substitutions`);
  }

  async addRule(rule: Omit<KhSubstitutionRule, "id">) {
    return await this.requests.post<KhSubstitutionRule>(`${base}/substitutions`, rule);
  }

  async deleteRule(id: string) {
    return await this.requests.delete<undefined>(`${base}/substitutions/${encodeURIComponent(id)}`);
  }

  /** Saves a copy with the ALLERGENS replaced; 422 when nothing can be replaced. */
  async makeVariant(slug: string, allergens: KhAllergenKey[]) {
    return await this.requests.post<{ slug: string }>(`${base}/recipes/${encodeURIComponent(slug)}/variant`, { allergens });
  }
}
