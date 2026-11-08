<!-- KH: the running timers (D42): a list under the step in cook mode, a thin bar above the bottom bar on the recipe
page (`compact`). A timer that has run out rings until "Aus" is tapped. -->
<template>
  <v-footer
    v-if="rows.length"
    :app="compact"
    :color="compact ? undefined : 'transparent'"
    class="d-print-none flex-column align-stretch ga-1 pa-2"
    role="region"
    :aria-label="$t('kh.timer.list')"
  >
    <div v-for="row in rows" :key="row.timer.id" class="d-flex align-center ga-2" :class="{ 'text-primary': row.done }">
      <NuxtLink v-if="isOtherRecipe(row.timer)" :to="recipeLink(row.timer)" class="flex-grow-1 text-truncate py-3">
        {{ row.timer.label }}
      </NuxtLink>
      <span v-else class="flex-grow-1 text-truncate">{{ row.timer.label }}</span>

      <strong class="text-h6 kh-timer-time">{{ row.done ? $t("kh.timer.done") : format(row.left) }}</strong>

      <template v-if="row.done">
        <v-btn v-if="row.timer.extraSeconds" size="large" variant="tonal" @click="extend(row.timer.id)">
          {{ $t("kh.timer.more", { n: Math.ceil(row.timer.extraSeconds / 60) }) }}
        </v-btn>
        <v-btn size="large" color="primary" @click="stop(row.timer.id)">
          {{ $t("kh.timer.off") }}
        </v-btn>
      </template>
      <template v-else>
        <v-btn
          icon
          variant="text"
          :aria-label="row.timer.pausedLeft === null ? $t('kh.timer.pause') : $t('kh.timer.resume')"
          @click="row.timer.pausedLeft === null ? pause(row.timer.id) : resume(row.timer.id)"
        >
          <v-icon>{{ row.timer.pausedLeft === null ? $globals.icons.pause : $globals.icons.play }}</v-icon>
        </v-btn>
        <v-btn icon variant="text" :aria-label="$t('kh.timer.stop')" @click="stop(row.timer.id)">
          <v-icon>{{ $globals.icons.close }}</v-icon>
        </v-btn>
      </template>
    </div>
  </v-footer>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from "vue";
import { startAlarm, useKhTimers, type KhTimer } from "../composables/use-kh-timers";

defineProps<{ compact?: boolean }>();

const route = useRoute();
const auth = useMealieAuth();
const { timers, ringing, tick, left, done, pause, resume, stop, extend } = useKhTimers();

// `tick` makes the list read the clock again every second.
const rows = computed(() => {
  void tick.value;
  return timers.value.map(timer => ({ timer, left: left(timer), done: done(timer) }));
});

const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");

/** Whether TIMER belongs to a recipe other than the one on screen. */
function isOtherRecipe(timer: KhTimer): boolean {
  return timer.recipeSlug !== route.params.slug;
}

/** The address of the recipe TIMER belongs to. */
function recipeLink(timer: KhTimer): string {
  return `/g/${groupSlug.value}/r/${timer.recipeSlug}`;
}

/** SECONDS as m:ss, or h:mm:ss from an hour on. */
function format(seconds: number): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const hours = Math.floor(seconds / 3600);
  const rest = `${hours ? pad(Math.floor(seconds / 60) % 60) : Math.floor(seconds / 60)}:${pad(seconds % 60)}`;
  return hours ? `${hours}:${rest}` : rest;
}

// One alarm for all ringing timers, from the first one running out until none is left.
let stopAlarm: (() => void) | undefined;
watch(() => ringing.value.length > 0, (ringingNow) => {
  if (ringingNow) {
    stopAlarm ??= startAlarm();
  }
  else {
    stopAlarm?.();
    stopAlarm = undefined;
  }
}, { immediate: true });
onBeforeUnmount(() => stopAlarm?.());
</script>

<style scoped>
.kh-timer-time {
  font-variant-numeric: tabular-nums;
}
</style>
