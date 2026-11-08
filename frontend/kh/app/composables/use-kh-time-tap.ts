// KH: a tap on a time in a step text starts a timer (D42). Mealie's step list and the step view share this handler.
import { useKhTimers, unlockAudio } from "./use-kh-timers";
import { khStepDisplay, timeIndex, timerLabel } from "../lib/step-text";
import type { Recipe, RecipeStep } from "~/lib/api/types/recipe";

/** The click handler for the element that holds the text of step PLACE: a tap on a time starts its timer and
 * goes no further (so Mealie's tick-off of the step does not fire); a tap elsewhere is left alone. */
export function useKhTimeTap() {
  const { start } = useKhTimers();

  return function onStepTextClick(event: MouseEvent, place: number, step: RecipeStep, recipe: Recipe, scale: number): void {
    const index = timeIndex(event.target, event.currentTarget as HTMLElement);
    if (index < 0) return;
    event.stopPropagation();
    unlockAudio();
    const time = khStepDisplay(place, step, recipe, scale).times[index];
    if (time) start(time, timerLabel(place, step.text ?? ""), recipe.slug ?? "", place);
  };
}
