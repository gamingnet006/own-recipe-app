<!-- KH: cook mode shows one step at a time (D42): progress, what the step needs, its text in big type, the running
timers and two big buttons. Swiping, the arrow keys and the space bar move between steps; the screen stays on. -->
<template>
  <div ref="area" class="kh-cook mx-auto px-4">
    <div class="d-flex align-center justify-space-between py-1">
      <v-btn icon variant="text" :aria-label="$t('kh.cook.leave')" @click="$emit('close')">
        <v-icon>{{ $globals.icons.close }}</v-icon>
      </v-btn>
      <v-btn variant="text" size="large" @click="$emit('all-steps')">
        {{ $t("kh.cook.all-steps") }}
      </v-btn>
    </div>

    <v-alert v-if="(!lock.isSupported.value || lockFailed) && !lockHintSeen" type="info" closable class="mb-2" @click:close="lockHintSeen = true">
      {{ $t("kh.cook.lock-hint") }}
    </v-alert>

    <p v-if="!total" class="text-h6 my-6">
      {{ $t("kh.cook.no-steps") }}
    </p>
    <template v-else>
      <div v-if="showsSegments(total)" class="d-flex ga-1">
        <button
          v-for="n in total"
          :key="n"
          type="button"
          class="kh-segment"
          :aria-label="$t('kh.cook.step', { n })"
          :aria-current="n - 1 === cook.step.value ? 'step' : undefined"
          @click="cook.goTo(n - 1)"
        >
          <span :class="n - 1 < cook.step.value ? 'kh-done' : n - 1 === cook.step.value ? 'kh-current' : ''" />
        </button>
      </div>
      <v-progress-linear v-else :model-value="((cook.step.value + 1) / total) * 100" height="8" rounded class="my-2" />
      <p class="text-body-2 text-medium-emphasis">
        {{ $t("kh.cook.step-of", { n: cook.step.value + 1, total }) }}
      </p>

      <h2 v-if="current?.title" class="text-h6 mt-3">
        {{ current.title }}
      </h2>
      <p v-if="needs.length" class="text-body-1 text-medium-emphasis mt-3">
        {{ $t("kh.cook.you-need") }} {{ needs.join(" · ") }}
      </p>
      <SafeMarkdown
        v-if="current"
        class="kh-cook-text mt-3"
        :source="khStepDisplay(cook.step.value, current, recipe, scale).html"
        @click="onStepTextClick($event, cook.step.value, current, recipe, scale)"
      />
    </template>

    <KhTimers class="mt-4" />

    <div class="kh-cook-buttons d-flex ga-3 py-3">
      <v-btn size="x-large" variant="tonal" :disabled="cook.isFirst.value" @click="cook.back()">
        {{ $t("kh.cook.back") }}
      </v-btn>
      <v-btn size="x-large" color="primary" class="kh-forward" @click="cookForward(cook, () => emit('close'))">
        {{ cook.isLast.value ? $t("kh.cook.done") : $t("kh.cook.next") }}
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useEventListener, useLocalStorage, useSwipe, useWakeLock } from "@vueuse/core";
import { cookForward, handleCookKey, showsSegments, type KhCook } from "../composables/use-kh-cook";
import { useKhTimeTap } from "../composables/use-kh-time-tap";
import { timersListedInStep } from "../composables/use-kh-timers";
import { khStepDisplay, khStepNeeds } from "../lib/step-text";
import type { Recipe } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: Recipe; scale: number; cook: KhCook }>();
const emit = defineEmits<{ "close": []; "all-steps": [] }>();

const onStepTextClick = useKhTimeTap();
const area = ref<HTMLElement | null>(null);

const steps = computed(() => props.recipe.recipeInstructions ?? []);
const total = computed(() => steps.value.length);
const current = computed(() => steps.value[props.cook.step.value]);
const needs = computed(() => (current.value ? khStepNeeds(props.cook.step.value, current.value, props.recipe, props.scale) : []));

// A new step starts at the top of the page.
watch(props.cook.step, () => window.scrollTo({ top: 0 }));

useSwipe(area, {
  onSwipeEnd: (_event, direction) => {
    if (direction === "left") props.cook.next();
    else if (direction === "right") props.cook.back();
  },
});

useEventListener(window, "keydown", event => handleCookKey(props.cook, event));

// The screen stays on while the step view is open; where the device cannot, a hint says so once.
const lock = useWakeLock();
const lockFailed = ref(false);
const lockHintSeen = useLocalStorage("kh-cook-lock-hint-seen", false);
onMounted(() => {
  timersListedInStep.value = true;
  lock.request("screen").catch(() => (lockFailed.value = true));
});
onBeforeUnmount(() => {
  timersListedInStep.value = false;
  lock.release();
});
</script>

<style scoped>
.kh-cook {
  max-width: 720px;
}

.kh-segment {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 48px;
}

.kh-segment span {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.kh-segment .kh-done {
  background: rgb(var(--v-theme-primary));
  opacity: 0.45;
}

.kh-segment .kh-current {
  background: rgb(var(--v-theme-primary));
}

.kh-segment:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.kh-cook-text {
  font-size: 1.5rem;
  line-height: 1.55;
}

.kh-cook-text :deep(.kh-time) {
  padding: 4px 8px;
}

/* Always within reach, above the bar at the bottom. */
.kh-cook-buttons {
  position: sticky;
  bottom: var(--v-layout-bottom, 0px);
  background: rgb(var(--v-theme-background));
}

.kh-cook-buttons .v-btn {
  flex: 1;
}

.kh-cook-buttons .kh-forward {
  flex: 2;
}
</style>
