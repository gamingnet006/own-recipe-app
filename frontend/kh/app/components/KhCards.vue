<!-- KH: a dialog of short cards with an icon, a title and a sentence or two (D59, D69): the first-sign-in tour and "Neu in
Kochheft" share it. Full screen on a phone, a centred card on iPad and computers that never grows taller than the
window: the text scrolls inside, the buttons stay at the bottom. Finishing or skipping emits "done". A card with a
button emits "action" with the card's action name, and the dialog closes. -->
<template>
  <v-dialog
    :model-value="modelValue"
    :fullscreen="phone"
    max-width="640"
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card class="kh-cards d-flex flex-column" :class="{ 'kh-cards-phone': phone }">
      <p v-if="heading" class="text-overline text-center text-medium-emphasis pt-4 mb-0">
        {{ heading }}
      </p>
      <div class="kh-cards-body d-flex flex-column align-center justify-center text-center px-6 py-4">
        <v-icon :icon="card.icon" class="kh-cards-icon mb-4" color="primary" />
        <h2 class="text-h5 mb-3">
          {{ card.title }}
        </h2>
        <p class="text-body-1">
          {{ card.text }}
        </p>
        <v-btn
          v-if="card.action"
          color="primary"
          variant="tonal"
          size="large"
          class="mt-4"
          @click="act(card.action)"
        >
          {{ card.actionLabel }}
        </v-btn>
        <div class="mt-4">
          <span
            v-for="(_, i) in cards"
            :key="i"
            class="d-inline-block rounded-circle mx-1"
            :class="i === index ? 'bg-primary' : 'bg-grey-lighten-1'"
            style="width: 8px; height: 8px"
          />
        </div>
      </div>
      <v-card-actions class="px-4 pb-4">
        <v-btn variant="text" size="large" @click="finish">
          {{ $t("kh.tour.skip") }}
        </v-btn>
        <v-spacer />
        <v-btn v-if="index > 0" variant="text" size="large" @click="index--">
          {{ $t("kh.tour.back") }}
        </v-btn>
        <v-btn color="primary" variant="flat" size="large" @click="next">
          {{ last ? finishLabel : $t("kh.tour.next") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { useDisplay } from "vuetify";

export interface KhCard {
  /** An icon path, as $globals.icons holds them. */
  icon: string;
  title: string;
  text: string;
  /** Name of the card's action, with the button's text in actionLabel. */
  action?: string;
  actionLabel?: string;
}

const props = defineProps<{ modelValue: boolean; cards: KhCard[]; finishLabel: string; heading?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean]; "done": []; "action": [name: string] }>();

// Full screen only on phones (below Vuetify's "sm" breakpoint); iPad and computers get the centred card
const { xs: phone } = useDisplay();

const index = ref(0);
const card = computed(() => props.cards[index.value]!);
const last = computed(() => index.value === props.cards.length - 1);

// Opened again, it starts at the first card
watch(() => props.modelValue, (open) => {
  if (open) index.value = 0;
});

/** Goes to the next card; the last one finishes. */
function next() {
  if (last.value) finish();
  else index.value++;
}

/** Closes the dialog, finished or skipped. */
function finish() {
  emit("update:modelValue", false);
  emit("done");
}

/** The card's button: finishes the dialog and tells the page what to do. */
function act(name: string) {
  finish();
  emit("action", name);
}
</script>

<style scoped>
/* Never taller than the window (dvh: the phone's toolbar does not count); the body scrolls, the buttons stay. */
.kh-cards {
  max-height: min(720px, 92dvh);
}
.kh-cards-phone {
  max-height: none;
  height: 100%;
}
.kh-cards-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}
/* The picture shrinks with the window's height, so a landscape phone still fits the text */
.kh-cards-icon {
  font-size: clamp(56px, 14dvh, 112px);
}
</style>
