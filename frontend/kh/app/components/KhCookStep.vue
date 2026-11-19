<!-- KH: cook mode shows one step at a time (D42): progress, what the step needs, its text in big type, the running
timers and two big buttons. Swiping, the arrow keys and the space bar move between steps; the screen stays on. -->
<template>
  <div ref="area" class="kh-cook mx-auto px-4" :class="{ 'kh-cook-wide': wide, 'kh-cook-extra': asksMade }">
    <!-- wide landscape screens (D74): the ingredients stay in view at the left, the step is at the right -->
    <aside v-if="wide" class="kh-cook-ingredients">
      <RecipeIngredients
        :value="recipe.recipeIngredient"
        :scale="scale"
        is-cook-mode
        :storage-key="ingredientStorageKey"
        :highlight-ids="[...stepIngredientIds(current)]"
      />
    </aside>
    <div class="kh-cook-main">
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
        <v-progress-linear v-else :model-value="((cook.step.value + 1) / total) * 100" height="4" rounded class="my-2" />
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
          :source="khStepDisplay(cook.step.value, current, recipe, scale, khOn.oven ? oven : null).html"
          @click="onStepTextClick($event, cook.step.value, current, recipe, scale)"
        />
      </template>

      <KhTimers class="mt-4" />

      <KhCookVoice class="mt-4" :recipe="recipe" :scale="scale" :cook="cook" @close="emit('close')" />

      <div class="kh-cook-buttons d-flex ga-3">
        <!-- always in view: a small text button above the main buttons, inside the fixed bar -->
        <v-btn v-if="asksMade" variant="text" size="small" class="kh-close-only" @click="emit('close')">
          {{ $t("kh.cook.close-only") }}
        </v-btn>
        <v-btn size="x-large" variant="tonal" :disabled="cook.isFirst.value" @click="cook.back()">
          {{ $t("kh.cook.back") }}
        </v-btn>
        <!-- on the last step the one green button notes the dish as cooked (Mealie's "I made this" dialog) -->
        <v-btn
          v-if="asksMade"
          size="x-large"
          color="primary"
          class="kh-forward"
          :prepend-icon="$globals.icons.chefHat"
          @click="madeThis = true"
        >
          {{ $t("kh.cook.done-made") }}
        </v-btn>
        <v-btn v-else size="x-large" color="primary" class="kh-forward" @click="cookForward(cook, () => emit('close'))">
          {{ cook.isLast.value ? $t("kh.cook.done") : $t("kh.cook.next") }}
        </v-btn>
      </div>
      <RecipeLastMade
        v-if="isOwnGroup"
        v-model:dialog="madeThis"
        :recipe="recipe"
        :submit-text="$t('kh.cook.save-made')"
        class="d-none"
        @event-created="cook.finish()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useEventListener, useLocalStorage, useMediaQuery, useSwipe, useWakeLock } from "@vueuse/core";
import { cookForward, handleCookKey, showsSegments, type KhCook } from "../composables/use-kh-cook";
import { useKhTimeTap } from "../composables/use-kh-time-tap";
import { timersListedInStep } from "../composables/use-kh-timers";
import { useKhOn } from "../composables/use-kh-addons";
import { useKhOven } from "../lib/oven";
import { khStepDisplay, khStepNeeds, stepIngredientIds } from "../lib/step-text";
import type { RecipeOut } from "~/lib/api/types/recipe";
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const props = defineProps<{ recipe: RecipeOut; scale: number; cook: KhCook; ingredientStorageKey?: string }>();
const emit = defineEmits<{ "close": []; "all-steps": [] }>();
const { isOwnGroup } = useLoggedInState();
const madeThis = ref(false); // the "I made this" dialog, opened from the last step
const asksMade = computed(() => props.cook.isLast.value && isOwnGroup.value);

// Two columns on wide landscape screens (iPad lying down, Mac); phones and upright iPads keep the single column.
const wide = useMediaQuery("(min-width: 1024px) and (orientation: landscape)");

const onStepTextClick = useKhTimeTap();
// Read while rendering (khStepDisplay needs the render context), never from a click handler.
const oven = useKhOven();
const khOn = useKhOn();
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
  /* room for the fixed buttons, so they never cover the end of the step */
  padding-bottom: calc(96px + env(safe-area-inset-bottom, 0px));
}

.kh-segment {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 24px; /* a thin line, but still easy to tap */
  padding: 0;
  border: 0;
  background: transparent;
}

.kh-segment span {
  width: 100%;
  height: 4px;
  border-radius: 2px;
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

/* wide landscape (D74): ingredients left, step right; the bar at the bottom starts where the right column does */
.kh-cook-wide {
  --kh-cook-side: 380px;
  max-width: 1360px;
  display: grid;
  grid-template-columns: var(--kh-cook-side) 1fr;
  column-gap: 32px;
  align-items: start;
}

.kh-cook-ingredients {
  position: sticky;
  top: 0;
  max-height: calc(100vh - 96px - var(--v-layout-bottom, 0px));
  overflow-y: auto;
  padding-top: 8px;
}

.kh-cook-wide .kh-cook-main {
  max-width: 800px;
}

.kh-cook-wide .kh-cook-buttons {
  padding-inline-start: max(16px, calc((100% - 1360px) / 2 + 16px + var(--kh-cook-side) + 32px));
  padding-inline-end: max(16px, calc((100% - 1360px) / 2 + 16px));
}

.kh-cook-text {
  font-size: 1.5rem;
  line-height: 1.55;
}

.kh-cook-text :deep(.kh-time) {
  padding: 4px 8px;
}

/* Always at the same place, right above the bar at the bottom, so only that spot of the screen gets touched while
   cooking (user's wish, 8.11.2026). */
.kh-cook-buttons {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--v-layout-bottom, 0px);
  z-index: 5;
  padding-top: 12px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  padding-inline: max(16px, calc((100% - 720px) / 2));
  background: rgb(var(--v-theme-background));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.kh-cook-buttons {
  flex-wrap: wrap;
}

.kh-cook-buttons .v-btn {
  flex: 1;
}

.kh-cook-buttons .kh-close-only {
  flex: 0 0 100%;
}

/* the extra row of the bar on the last step */
.kh-cook-extra {
  padding-bottom: calc(140px + env(safe-area-inset-bottom, 0px));
}

.kh-cook-buttons .kh-forward {
  flex: 2;
}
</style>
