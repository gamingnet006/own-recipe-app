<!-- KH: the detail sheet of the shopping page (D60), opened when something is written down or held: amount,
properties, urgency, "always in the house" (D65) and an own note. Every tap saves at once; the note is saved a moment
after typing. -->
<template>
  <v-bottom-sheet :model-value="!!item" @update:model-value="onToggle">
    <v-card v-if="item" class="kh-sheet pa-4" rounded="t-xl">
      <h3 class="text-h6 font-weight-bold">
        {{ $t("kh.shopping.details-title", { name: itemTitle(item, units) }) }}
      </h3>
      <p v-if="recipeName" class="text-body-2 text-medium-emphasis mt-1">
        {{ $t("kh.shopping.from-recipe", { name: recipeName }) }}
      </p>

      <div class="kh-sheet__label">
        {{ $t("kh.shopping.quantity") }}
      </div>
      <div class="kh-sheet__chips">
        <v-chip
          v-for="chip in quantityChips"
          :key="chip"
          :color="sameAmount(chip, quantityText(item)) ? 'primary' : undefined"
          :variant="sameAmount(chip, quantityText(item)) ? 'flat' : 'tonal'"
          @click="emit('quantity', item, chip)"
        >
          {{ chip }}
        </v-chip>
      </div>

      <div class="kh-sheet__label">
        {{ $t("kh.shopping.properties") }}
      </div>
      <div class="kh-sheet__chips">
        <v-chip
          v-for="chip in PROPERTY_CHIPS"
          :key="chip"
          :color="properties.includes(chip) ? 'primary' : undefined"
          :variant="properties.includes(chip) ? 'flat' : 'tonal'"
          @click="emit('change', item, { note: toggleProperty(item.note, chip) })"
        >
          {{ chip }}
        </v-chip>
      </div>

      <div class="kh-sheet__label">
        {{ $t("kh.shopping.urgency") }}
      </div>
      <div class="kh-sheet__chips">
        <v-chip
          v-for="entry in URGENCY"
          :key="entry.key"
          :prepend-icon="entry.icon"
          :color="entry.key === urgency ? 'primary' : undefined"
          :variant="entry.key === urgency ? 'flat' : 'tonal'"
          @click="setUrgency(entry.key)"
        >
          {{ $t(entry.labelKey) }}
        </v-chip>
      </div>

      <v-switch
        v-if="item.food"
        :model-value="onHand"
        :label="$t('kh.shopping.on-hand')"
        color="primary"
        density="compact"
        hide-details
        class="mt-2"
        @update:model-value="emit('onHand', item.food.id, !!$event)"
      />

      <v-text-field
        v-model="ownText"
        :placeholder="$t('kh.shopping.own-note')"
        variant="solo-filled"
        flat
        hide-details
        class="mt-4"
        @update:model-value="saveSoon"
        @keydown.enter="finish"
      />

      <div class="d-flex ga-2 mt-4">
        <v-btn variant="tonal" @click="emit('remove', item)">
          {{ $t("kh.shopping.remove") }}
        </v-btn>
        <v-btn color="primary" class="flex-grow-1" @click="finish">
          {{ $t("kh.shopping.done") }}
        </v-btn>
      </div>
    </v-card>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { IngredientUnitOut } from "~/lib/api/types/recipe";
import {
  PROPERTY_CHIPS,
  QUANTITY_CHIPS,
  URGENCY,
  URGENCY_EXTRA,
  type Urgency,
  itemTitle,
  quantityText,
  sameAmount,
  splitNote,
  toggleProperty,
  urgencyOf,
  withOwnText,
} from "../lib/shopping-items";
import type { ItemChanges } from "../composables/use-kh-shopping";

const props = defineProps<{
  item: ShoppingListItemOut | null;
  units: IngredientUnitOut[];
  recipes: Record<string, string>;
  /** Whether the item's food is always in the house (D65) */
  onHand: boolean;
}>();
const emit = defineEmits<{
  change: [item: ShoppingListItemOut, changes: ItemChanges];
  quantity: [item: ShoppingListItemOut, chip: string];
  remove: [item: ShoppingListItemOut];
  onHand: [foodId: string, value: boolean];
  close: [];
}>();

const SAVE_DELAY_MS = 600;

const properties = computed(() => splitNote(props.item?.note ?? null).properties);
const urgency = computed(() => (props.item ? urgencyOf(props.item) : ""));
const recipeName = computed(() => props.recipes[props.item?.recipeReferences[0]?.recipeId ?? ""]);
// An amount the chips do not offer (from a recipe, say) stands in front of them, so it can be seen and replaced.
const quantityChips = computed(() => {
  const current = props.item ? quantityText(props.item) : "";
  return current && !QUANTITY_CHIPS.some(chip => sameAmount(chip, current)) ? [current, ...QUANTITY_CHIPS] : QUANTITY_CHIPS;
});

const ownText = ref("");
watch(() => props.item?.id, () => {
  ownText.value = props.item ? splitNote(props.item.note).own : "";
}, { immediate: true });

/** Saves the note's own text if it changed; a note-only item's own text is its name, which may not be empty. */
function saveNote() {
  const item = props.item;
  if (!item) return;
  const text = ownText.value.trim();
  if (text === splitNote(item.note).own || (!item.food && !text)) return;
  emit("change", item, { note: withOwnText(item.note, text) });
}
const saveSoon = useDebounceFn(saveNote, SAVE_DELAY_MS);

function finish() {
  saveNote();
  emit("close");
}

function onToggle(open: boolean) {
  if (!open) finish();
}

/** A tap on the chosen urgency takes it away. */
function setUrgency(key: Urgency) {
  const item = props.item;
  if (!item) return;
  const { [URGENCY_EXTRA]: _, ...rest } = item.extras ?? {};
  emit("change", item, { extras: key === urgency.value ? rest : { ...rest, [URGENCY_EXTRA]: key } });
}
</script>

<style scoped>
.kh-sheet {
  max-width: 560px;
  margin: 0 auto;
}

.kh-sheet__label {
  margin-top: 14px;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.kh-sheet__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
