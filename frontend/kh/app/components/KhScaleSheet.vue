<!-- KH: "Umrechnen" (D39, A3): the recipe's amounts by servings, by "I only have …" of one ingredient, or from one pan
     to another. The factor only changes the view; "Übernehmen" stays off while the input is no usable number. -->
<template>
  <v-bottom-sheet v-model="open">
    <v-card :title="$t('kh.amounts.scale.title')">
      <v-tabs v-model="way" grow>
        <v-tab value="servings" :disabled="!base">
          {{ $t("kh.amounts.scale.servings") }}
        </v-tab>
        <v-tab value="have" :disabled="!lines.length">
          {{ $t("kh.amounts.scale.have-only") }}
        </v-tab>
        <v-tab value="pan">
          {{ $t("kh.amounts.scale.pan") }}
        </v-tab>
      </v-tabs>
      <v-card-text>
        <v-window v-model="way">
          <v-window-item value="servings">
            <v-text-field
              v-model.number="servings"
              type="number"
              inputmode="decimal"
              :label="$t('kh.amounts.scale.servings')"
              :prepend-inner-icon="$globals.icons.minus"
              :append-inner-icon="$globals.icons.createAlt"
              @click:prepend-inner="servings = Math.max(1, Math.ceil(servings) - 1)"
              @click:append-inner="servings = Math.floor(servings) + 1"
            />
          </v-window-item>
          <v-window-item value="have">
            <v-select
              v-model="lineIndex"
              :items="lines"
              item-title="title"
              item-value="index"
              :label="$t('kh.amounts.scale.ingredient')"
            />
            <v-text-field
              v-model.number="have"
              type="number"
              inputmode="decimal"
              :label="$t('kh.amounts.scale.amount')"
              :suffix="unitText"
            />
          </v-window-item>
          <v-window-item value="pan">
            <div v-for="(pan, index) in pans" :key="index" class="mb-2">
              <div class="text-subtitle-2 mb-1">
                {{ $t(index ? "kh.amounts.scale.new" : "kh.amounts.scale.old") }}
              </div>
              <v-btn-toggle v-model="pan.shape" mandatory density="compact" variant="outlined" class="mb-2">
                <v-btn value="round">
                  {{ $t("kh.amounts.scale.round") }}
                </v-btn>
                <v-btn value="rect">
                  {{ $t("kh.amounts.scale.rect") }}
                </v-btn>
              </v-btn-toggle>
              <v-text-field
                v-if="pan.shape === 'round'"
                v-model.number="pan.diameter"
                type="number"
                inputmode="decimal"
                :label="$t('kh.amounts.scale.diameter')"
              />
              <div v-else class="d-flex ga-2">
                <v-text-field v-model.number="pan.length" type="number" inputmode="decimal" :label="$t('kh.amounts.scale.length')" />
                <v-text-field v-model.number="pan.width" type="number" inputmode="decimal" :label="$t('kh.amounts.scale.width')" />
              </div>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" variant="flat" :disabled="factor === null" @click="apply">
          {{ $t("kh.amounts.scale.apply") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
import { haveOnlyFactor, panFactor, parsePan, servingsFactor, type KhPan } from "../lib/amounts";
import { scaleBase } from "../composables/use-kh-recipe";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { RecipeOut } from "~/lib/api/types/recipe";

type PanForm = { shape: "round" | "rect"; diameter?: number; length?: number; width?: number };

const props = defineProps<{ recipe: NoUndefinedField<RecipeOut> }>();
const open = defineModel<boolean>({ required: true });
const scale = defineModel<number>("scale", { required: true });

const base = computed(() => scaleBase(props.recipe));
// the lines with an amount, for "I only have …"
const lines = computed(() =>
  props.recipe.recipeIngredient
    .map((line, index) => ({ index, line, title: line.display || line.note || "" }))
    .filter(item => !!item.line.quantity),
);
const way = ref(base.value ? "servings" : "have");
const servings = ref(base.value);
const lineIndex = ref(lines.value[0]?.index);
const have = ref<number>();
// the yield's number and text joined again: Mealie's import moves "26" out of "Springform Ø 26 cm"
const oldPan = parsePan([props.recipe.recipeYieldQuantity, props.recipe.recipeYield].filter(Boolean).join(" "));
const pans = reactive<PanForm[]>([{ shape: "round", ...oldPan }, { shape: oldPan?.shape ?? "round" }]);

const chosen = computed(() => props.recipe.recipeIngredient[lineIndex.value ?? -1]);
const unitText = computed(() => {
  const unit = chosen.value?.unit;
  return (unit?.useAbbreviation ? unit.abbreviation : unit?.name) || "";
});

/** The pan the form describes; a field left empty makes it unusable. */
function toPan(form: PanForm): KhPan {
  return form.shape === "round"
    ? { shape: "round", diameter: Number(form.diameter) }
    : { shape: "rect", length: Number(form.length), width: Number(form.width) };
}

const factor = computed(() => {
  if (way.value === "servings") return servingsFactor(Number(servings.value), base.value);
  if (way.value === "have") return haveOnlyFactor(Number(have.value), chosen.value?.quantity ?? 0);
  return panFactor(toPan(pans[0]!), toPan(pans[1]!));
});

// each time the sheet opens, the servings start from what the page shows now
watch(open, (isOpen) => {
  if (isOpen) servings.value = Number((base.value * scale.value).toFixed(2));
});

function apply() {
  if (factor.value === null) return;
  scale.value = factor.value;
  open.value = false;
}
</script>
