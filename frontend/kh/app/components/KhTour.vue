<!-- KH: the first-sign-in tour (D59): a few short steps with an icon, a title and a sentence or two. Full screen on a
phone, a card on bigger screens. Finishing or skipping closes it and emits "done". -->
<template>
  <v-dialog
    :model-value="modelValue"
    :fullscreen="mobile"
    max-width="560"
    persistent
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card class="d-flex flex-column" :height="mobile ? '100%' : 480">
      <v-card-text class="d-flex flex-column align-center justify-center text-center flex-grow-1">
        <v-icon :icon="icon(step.icon)" size="96" color="primary" class="mb-6" />
        <h2 class="text-h5 mb-3">
          {{ $t(`kh.tour.steps.${step.key}.title`) }}
        </h2>
        <p class="text-body-1">
          {{ $t(`kh.tour.steps.${step.key}.text`) }}
        </p>
        <div class="mt-6">
          <span
            v-for="(_, i) in steps"
            :key="i"
            class="d-inline-block rounded-circle mx-1"
            :class="i === index ? 'bg-primary' : 'bg-grey-lighten-1'"
            style="width: 8px; height: 8px"
          />
        </div>
      </v-card-text>
      <v-card-actions class="px-4 pb-4">
        <v-btn variant="text" @click="finish">
          {{ $t("kh.tour.skip") }}
        </v-btn>
        <v-spacer />
        <v-btn v-if="index > 0" variant="text" @click="index--">
          {{ $t("kh.tour.back") }}
        </v-btn>
        <v-btn color="primary" variant="flat" @click="next">
          {{ last ? $t("kh.tour.start") : $t("kh.tour.next") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { useDisplay } from "vuetify";
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { tourSteps } from "~~/kh/app/lib/tour";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean]; "done": [] }>();

const { $globals } = useNuxtApp();
const { smAndDown: mobile } = useDisplay();

const steps = computed(() => tourSteps(khAddons.enabled));
const index = ref(0);
const step = computed(() => steps.value[index.value]!);
const last = computed(() => index.value === steps.value.length - 1);

// A tour opened again starts at the first step
watch(() => props.modelValue, (open) => {
  if (open) index.value = 0;
});

/** One of Mealie's icons by its name in the list of steps. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}

/** Goes to the next step; the last one finishes. */
function next() {
  if (last.value) finish();
  else index.value++;
}

/** Closes the tour, finished or skipped. */
function finish() {
  emit("update:modelValue", false);
  emit("done");
}
</script>
