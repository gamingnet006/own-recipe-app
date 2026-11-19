<!-- KH: "Als Text teilen" (D61): one recipe as plain text for a message, a note or a file, for the servings chosen here
     (the dialog starts with the ones chosen on the recipe page). -->
<template>
  <v-dialog v-model="open" max-width="600" scrollable>
    <v-card :title="$t('kh.export.title')">
      <v-card-text>
        <div class="d-flex align-center ga-2 mb-3">
          <span class="flex-grow-1">{{ $t(base ? "kh.export.servings" : "kh.export.factor") }}</span>
          <v-btn icon variant="text" :aria-label="$t('kh.amounts.scale.fewer')" @click="change(-1)">
            <v-icon :icon="$globals.icons.minus" />
          </v-btn>
          <strong class="kh-count">{{ shown }}</strong>
          <v-btn icon variant="text" :aria-label="$t('kh.amounts.scale.more')" @click="change(1)">
            <v-icon :icon="$globals.icons.createAlt" />
          </v-btn>
        </div>
        <pre class="kh-text-preview">{{ preview }}</pre>
      </v-card-text>
      <v-card-actions class="flex-wrap">
        <v-btn :prepend-icon="$globals.icons.shareVariant" color="primary" variant="flat" @click="share">
          {{ $t("kh.export.share") }}
        </v-btn>
        <v-btn :prepend-icon="$globals.icons.contentCopy" variant="tonal" @click="copy">
          {{ $t("kh.export.copy") }}
        </v-btn>
        <v-btn :prepend-icon="$globals.icons.download" variant="tonal" @click="save">
          {{ $t("kh.export.save") }}
        </v-btn>
        <v-spacer />
        <v-btn variant="text" @click="open = false">
          {{ $t("general.close") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { copyText, saveFile, shareText, useRecipeText } from "../composables/use-kh-recipe-text";
import { stepScale } from "../composables/use-kh-recipe";
import { khAmounts } from "../lib/amounts-store";
import { safeFileName } from "../lib/zip";
import { alert } from "~/composables/use-toast";
import type { RecipeOut } from "~/lib/api/types/recipe";

const props = defineProps<{
  recipe: RecipeOut;
  /** The factor the recipe page shows now (1: the recipe's own servings). */
  scale: number;
}>();
const open = defineModel<boolean>({ required: true });

const i18n = useI18n();
const { $globals } = useNuxtApp();
const { loadAmounts, text } = useRecipeText();

const factor = ref(props.scale);
const base = computed(() => props.recipe.recipeServings || 0);
const shown = computed(() => {
  const number = new Intl.NumberFormat(i18n.locale.value, { maximumFractionDigits: 1, useGrouping: false });
  return base.value ? number.format(base.value * factor.value) : `×${number.format(factor.value)}`;
});
const preview = computed(() => text(props.recipe, factor.value));

// opened anew: the page's servings, and the recipe's amounts as its page reads them (a card in a list has none loaded)
let before: Awaited<ReturnType<typeof loadAmounts>> | undefined;
watch(open, async (isOpen) => {
  if (!isOpen) {
    if (before) khAmounts.value = before; // the page's own amounts come back
    return;
  }
  factor.value = props.scale;
  before = await loadAmounts(props.recipe);
}, { immediate: true }); // the dialog is mounted when it opens

/** One serving more or less (never below one); without servings the factor goes by whole numbers. */
function change(delta: 1 | -1) {
  factor.value = base.value ? stepScale(base.value, factor.value, delta) : Math.max(1, Math.round(factor.value) + delta);
}

async function copy() {
  const copied = await copyText(preview.value);
  if (copied) alert.success(i18n.t("kh.export.copied"));
  else alert.error(i18n.t("kh.export.copy-failed"));
}

/** The device's share menu; without one (or if it fails) the text is copied. */
async function share() {
  if (!(await shareText(props.recipe.name ?? "", preview.value))) await copy();
}

function save() {
  saveFile(`${safeFileName(props.recipe.name ?? "")}.txt`, preview.value, "text/plain;charset=utf-8");
}
</script>

<style scoped>
.kh-count {
  min-width: 3ch;
  text-align: center;
}

.kh-text-preview {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
