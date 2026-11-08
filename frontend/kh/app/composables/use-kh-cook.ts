// KH: where the step view of cook mode stands (D42): the current step, kept in the address as `step`, Next and Back
// within the recipe's steps, and whether Mealie's list of all steps is shown instead.
import { computed, ref, watch } from "vue";
import { useRouteQuery } from "~/composables/use-router";

/** Up to this many steps the progress bar has one segment per step, tappable; beyond it is one continuous bar. */
export const SEGMENT_MAX = 12;

/** The position in a recipe of TOTAL() steps; `step` is 0-based, `step=3` in the address means index 2. */
export function useKhCook(total: () => number) {
  const query = useRouteQuery<string>("step", "");
  const clamp = (index: number) => Math.min(Math.max(index, 0), Math.max(total() - 1, 0));

  // The address is read once, at the start; after that the step only goes into it.
  const index = ref(clamp(parseInt(query.value, 10) - 1 || 0));
  const step = computed(() => clamp(index.value));
  watch(step, value => (query.value = String(value + 1)));

  const allSteps = ref(false);
  const isFirst = computed(() => step.value === 0);
  const isLast = computed(() => step.value >= total() - 1);

  /** Moves to step I, kept within the recipe's steps. */
  function goTo(i: number): void {
    index.value = clamp(i);
  }

  return { step, allSteps, isFirst, isLast, goTo, next: () => goTo(step.value + 1), back: () => goTo(step.value - 1) };
}

export type KhCook = ReturnType<typeof useKhCook>;
