// KH: the review's tag chips (wave 2): which tags the recipe starts with, adding one without doubles, and turning
// a person's ticks in the proposal list into what is sent.
import type { KhTagProposal, KhTagRef } from "./api/tags";

/** The tags a draft's recipe came with (the group's own, chosen by the rules or the AI); tags without an ID are
 * skipped, because only existing tags may be kept. */
export function recognizedTags(recipe: { tags?: { id?: string | null; name: string; slug?: string | null }[] } | null): KhTagRef[] {
  return (recipe?.tags ?? []).flatMap(tag => (tag.id ? [{ id: tag.id, name: tag.name, slug: tag.slug ?? "" }] : []));
}

/** The chosen tags plus TAG, once. */
export function withTag(chosen: KhTagRef[], tag: KhTagRef): KhTagRef[] {
  return chosen.some(own => own.id === tag.id) ? chosen : [...chosen, tag];
}

/** What the proposal page sends: for each recipe the tags still ticked; recipes with none ticked are left out.
 * UNTICKED holds "recipeId:tagId" for every tag the person took away. */
export function confirmedItems(proposals: KhTagProposal[], unticked: Set<string>) {
  return proposals
    .map(proposal => ({
      recipeId: proposal.recipeId,
      tagIds: proposal.tags.map(tag => tag.id).filter(id => !unticked.has(`${proposal.recipeId}:${id}`)),
    }))
    .filter(item => item.tagIds.length > 0);
}
