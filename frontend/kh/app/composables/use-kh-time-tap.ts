// KH: a tap on a time in a step text starts a timer (D42). Mealie's step list and the step view share this handler.
import { useKhTimers, unlockAudio } from "./use-kh-timers";
import { khStepTimes, timeIndex, timerLabel } from "../lib/step-text";
import type { RecipeOut, RecipeStep } from "~/lib/api/types/recipe";

/** The click handler for the element that holds the text of step PLACE: a tap on a time starts its timer and
 * goes no further (so Mealie's tick-off of the step does not fire); a tap elsewhere is left alone. */
export function useKhTimeTap() {
  const { start } = useKhTimers();
  const { t } = useI18n();

  return function onStepTextClick(event: MouseEvent, place: number, step: RecipeStep, recipe: RecipeOut, scale: number): void {
    const index = timeIndex(event.target, event.currentTarget as HTMLElement);
    if (index < 0) return;
    event.stopPropagation();
    unlockAudio();
    const time = khStepTimes(place, step, recipe, scale)[index];
    if (time) start(time, timerLabel(place, time.seconds, t), recipe.slug ?? "", place);
  };
}
