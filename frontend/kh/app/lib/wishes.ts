// KH: the pure parts of the wish list (D72): who wishes a recipe, said the way people talk.
import type { KhWish } from "./api/wishes";

/** "Anna", "Anna und Opa", "Anna, Opa und Mama": the signed-in person (OWNID) shows as SELF and comes first. */
export function wishers(wish: Pick<KhWish, "people">, ownId: string | undefined, self: string): string[] {
  const names = wish.people.map(person => person.id === ownId ? self : person.name);
  return [...names.filter(name => name === self), ...names.filter(name => name !== self)];
}

/** Joins NAMES with commas and AND before the last one. */
export function joinNames(names: string[], and: string): string {
  return names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} ${and} ${names[names.length - 1]}`;
}

/** Whether the person has wished the recipe already. */
export function isWishedBy(wish: Pick<KhWish, "people"> | undefined, ownId: string | undefined): boolean {
  return !!wish && !!ownId && wish.people.some(person => person.id === ownId);
}
