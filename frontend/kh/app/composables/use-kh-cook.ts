// KH: where the step view of cook mode stands (D42): the current step, kept in the address as `step`, Next and Back
// within the recipe's steps, and whether Mealie's list of all steps is shown instead.
import { computed, ref, watch } from "vue";
import { useRouteQuery } from "~/composables/use-router";

/** From this many steps on the progress bar is one continuous bar instead of one tappable segment per step. */
const SEGMENT_MAX = 12;

/** Whether a recipe of TOTAL steps gets one progress segment per step. */
export function showsSegments(total: number): boolean {
  return total < SEGMENT_MAX;
}

/** The position in a recipe of TOTAL() steps; `step` is 0-based, `step=3` in the address means index 2. Opening cook
 * mode (IS_OPEN turns true) starts at the step view, not at the list of all steps, and at the first step again when it
 * was left on the last one: the dish is done, the next time is a new start. */
export function useKhCook(total: () => number, isOpen: () => boolean = () => true) {
  const query = useRouteQuery<string>("step", "");
  const clamp = (index: number) => Math.min(Math.max(index, 0), Math.max(total() - 1, 0));

  // The address is read once, at the start; after that the step only goes into it.
  const index = ref(clamp(parseInt(query.value, 10) - 1 || 0));
  const step = computed(() => clamp(index.value));
  // The restart on opening is not written into the address: opening writes `cook` there at the same moment, and two
  // late writes of the address undo each other (Mealie's useRouteQuery spreads the query it saw before).
  let quiet = false;
  watch(step, (value) => {
    if (quiet) quiet = false;
    else query.value = String(value + 1);
  });

  const allSteps = ref(false);
  const isFirst = computed(() => step.value === 0);
  const isLast = computed(() => step.value >= total() - 1);
  watch(isOpen, (open) => {
    if (!open) return;
    allSteps.value = false;
    if (isLast.value && step.value !== 0) {
      quiet = true;
      index.value = 0;
    }
  });

  /** Moves to step I, kept within the recipe's steps. */
  function goTo(i: number): void {
    index.value = clamp(i);
  }

  return { step, allSteps, isFirst, isLast, goTo, next: () => goTo(step.value + 1), back: () => goTo(step.value - 1) };
}

/** "Weiter" goes on; on the last step "Fertig" calls CLOSE. The next opening starts at the first step again (see
 * useKhCook): resetting here would write the step into the address while closing, and the two late writes of the
 * address would undo each other (cook mode back in the address). */
export function cookForward(cook: KhCook, close: () => void): void {
  if (cook.isLast.value) close();
  else cook.next();
}

/** Arrow keys and the space bar move between steps, unless a field or a button has the key's job. */
export function handleCookKey(cook: KhCook, event: KeyboardEvent): void {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  const target = event.target instanceof HTMLElement ? event.target : null;
  if (target?.closest("input, textarea, select, [contenteditable]")) return;
  if (event.key === "ArrowRight") cook.next();
  else if (event.key === "ArrowLeft") cook.back();
  else if (event.key === " " && !target?.closest("button, a")) {
    event.preventDefault();
    cook.next();
  }
}

export type KhCook = ReturnType<typeof useKhCook>;
