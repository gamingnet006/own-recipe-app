// KH: pure helpers of the draft review (D55): the body of an edit made in the preview, the step links after such an
// edit, and which cookbooks stand for exactly one category. Free of Vue, so they are testable without it.
import type { KhStepAmount } from "./api/amounts";

export type KhEditTarget = { kind: "name" } | { kind: "ingredient" | "step"; index: number };
export type KhDraftEdit = { name: string } | { ingredient: { index: number; text: string } } | { step: { index: number; text: string } };

// Mealie's filter language for "in this category"; a cookbook made here gets it, one made by hand may carry CONTAINS ALL
const ONE_CATEGORY = /^\s*recipe_category\.id\s+(?:IN|CONTAINS ALL)\s*\[\s*"([^",\s]+)"\s*\]\s*$/;

/** The filter of a cookbook that holds exactly one category. */
export function cookbookFilter(categoryId: string): string {
  return `recipe_category.id IN ["${categoryId}"]`;
}

/** The request body for the new TEXT at TARGET, or null for an empty text. */
export function editBody(target: KhEditTarget, text: string): KhDraftEdit | null {
  const clean = text.trim();
  if (!clean) return null;
  if (target.kind === "name") return { name: clean };
  return target.kind === "ingredient"
    ? { ingredient: { index: target.index, text: clean } }
    : { step: { index: target.index, text: clean } };
}

type Link = Pick<KhStepAmount, "step" | "referenceId" | "text">;

/** The indices of the links the review kept, for the list AFTER an edit: a link is the same one if step, ingredient
 * and text match, equal ones in their order; a link that is gone drops out. */
export function remapLinked(before: Link[], after: Link[], kept: number[]): number[] {
  const key = (link: Link) => `${link.step}|${link.referenceId}|${link.text}`;
  const taken = new Set<number>();
  const places = before.map((link) => {
    const place = after.findIndex((other, i) => !taken.has(i) && key(other) === key(link));
    if (place >= 0) taken.add(place);
    return place;
  });
  return kept.map(index => places[index] ?? -1).filter(place => place >= 0);
}

interface CookbookLike {
  queryFilterString?: string;
}

/** The cookbooks whose filter is exactly one category, each with that category's ID. */
export function oneCategoryCookbooks<T extends CookbookLike>(cookbooks: T[]): { cookbook: T; categoryId: string }[] {
  return cookbooks.flatMap((cookbook) => {
    const categoryId = ONE_CATEGORY.exec(cookbook.queryFilterString ?? "")?.[1];
    return categoryId ? [{ cookbook, categoryId }] : [];
  });
}

/** The item with this name, ignoring case and surrounding spaces; so "+ New cookbook" reuses a category that exists. */
export function findByName<T extends { name: string }>(items: T[], name: string): T | undefined {
  const wanted = name.trim().toLowerCase();
  return items.find(item => item.name.trim().toLowerCase() === wanted);
}
