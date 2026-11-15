<!-- KH: the switch for the voice commands in cook mode (P7.5, a test: add-on "voice", off by default). The tap is
needed for the microphone; the words weiter, zurück, timer and stopp then do what the buttons and the first time of the
step do. Nothing leaves the device. -->
<template>
  <div v-if="khOn.voice" class="kh-voice">
    <v-btn variant="tonal" :prepend-icon="$globals.icons.microphone" @click="onToggle">
      {{ voice.status.value === "off" ? $t("kh.voice.start") : $t("kh.voice.stop") }}
    </v-btn>
    <p v-if="voice.status.value === 'loading'" class="text-body-2 mt-1">
      {{ $t("kh.voice.loading") }} {{ voice.progress.value }} %
    </p>
    <p v-else-if="voice.status.value === 'listening'" class="text-body-2 mt-1" role="status">
      {{ $t("kh.voice.listening") }}
      <span v-if="voice.heard.value">{{ $t("kh.voice.heard", { word: voice.heard.value }) }}</span>
    </p>
    <p v-if="voice.error.value" class="text-body-2 text-error mt-1" role="alert">
      {{ $t(`kh.voice.error-${voice.error.value}`) }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { cookForward, type KhCook } from "../composables/use-kh-cook";
import { useKhOn } from "../composables/use-kh-addons";
import { useKhVoice } from "../composables/use-kh-voice";
import { unlockAudio, useKhTimers } from "../composables/use-kh-timers";
import { khStepTimes, timerLabel } from "../lib/step-text";
import type { VoiceCommand } from "../lib/voice";
import type { RecipeOut } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: RecipeOut; scale: number; cook: KhCook }>();
const emit = defineEmits<{ close: [] }>();

const khOn = useKhOn();
const timers = useKhTimers();

/** Does what the heard word says; "timer" starts the first time of the step, like the first tap on it. */
function run(command: VoiceCommand): void {
  const place = props.cook.step.value;
  const step = props.recipe.recipeInstructions?.[place];
  if (command === "next") cookForward(props.cook, () => emit("close"));
  else if (command === "back") props.cook.back();
  else if (command === "stop") timers.timers.value.filter(timers.done).forEach(timer => timers.stop(timer.id));
  else {
    const time = step && khStepTimes(place, step, props.recipe, props.scale)[0];
    if (time && step) timers.start(time, timerLabel(place, step.text ?? ""), props.recipe.slug ?? "", place);
  }
}

const voice = useKhVoice(run);

// The tap also unlocks the alarm sound, which iOS only allows after a tap.
function onToggle(): void {
  void voice.toggle();
  unlockAudio();
}
</script>
