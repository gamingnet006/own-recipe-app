<!-- KH: "Als Textdateien exportieren" (D61): every recipe of the cookbook as a text file in a folder of a ZIP, with the
     photos beside them if wanted, for the servings of each recipe or one number for all. Recipes that fail are listed. -->
<template>
  <v-dialog v-model="open" max-width="500" :persistent="running">
    <v-card :title="$t('kh.export.book-title')">
      <v-card-text>
        <v-radio-group v-model="mode" :disabled="running" hide-details>
          <v-radio value="own" :label="$t('kh.export.as-recipe')" />
          <v-radio value="all" :label="$t('kh.export.for-all')" />
        </v-radio-group>
        <v-text-field
          v-if="mode === 'all'"
          v-model.number="servings"
          type="number"
          inputmode="numeric"
          min="1"
          :label="$t('kh.export.servings-all')"
          :disabled="running"
          class="mt-2"
        />
        <v-checkbox v-model="withPhotos" :label="$t('kh.export.with-photos')" :disabled="running" hide-details />
        <div v-if="running || finished" class="mt-4">
          <v-progress-linear :model-value="(done / recipes.length) * 100" height="8" rounded />
          <div class="mt-1 text-caption">
            {{ done }} / {{ recipes.length }}
          </div>
        </div>
        <v-alert v-if="finished && failed.length" type="warning" variant="tonal" density="compact" class="mt-3">
          {{ $t("kh.export.failed", { names: failed.join(", ") }) }}
        </v-alert>
        <v-alert v-else-if="finished" type="success" variant="tonal" density="compact" class="mt-3">
          {{ $t("kh.export.done") }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" :disabled="running" @click="open = false">
          {{ $t("general.close") }}
        </v-btn>
        <v-btn color="primary" variant="flat" :loading="running" :disabled="!usable" @click="run">
          {{ $t("kh.export.run") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { saveFile, useRecipeText } from "../composables/use-kh-recipe-text";
import { servingsFactor } from "../lib/amounts";
import { khAmounts } from "../lib/amounts-store";
import { photoExtension } from "../lib/recipe-text";
import { makeZip, safeFileName, uniqueNames, type ZipEntry } from "../lib/zip";
import { useStaticRoutes } from "~/composables/api";
import type { RecipeOut } from "~/lib/api/types/recipe";

const props = defineProps<{
  /** The cookbook's recipes in full (the book page has read them already). */
  recipes: RecipeOut[];
  cookbookName: string;
}>();
const open = defineModel<boolean>({ required: true });

const { loadAmounts, text } = useRecipeText();
const { recipeImage } = useStaticRoutes();

const mode = ref<"own" | "all">("own");
const servings = ref(4);
const withPhotos = ref(true);
const running = ref(false);
const finished = ref(false);
const done = ref(0);
const failed = ref<string[]>([]);
const usable = computed(() => props.recipes.length > 0 && (mode.value === "own" || servingsFactor(servings.value, 1) !== null));

/** The recipe's photo as a ZIP entry named like its text file; none for a recipe without one or one that cannot be read. */
async function photoEntry(recipe: RecipeOut, path: string): Promise<ZipEntry | null> {
  if (!recipe.id || !recipe.image) return null;
  const response = await fetch(recipeImage(recipe.id, recipe.image)).catch(() => null);
  if (!response?.ok) return null;
  return { name: `${path}.${photoExtension(response.headers.get("content-type"))}`, data: new Uint8Array(await response.arrayBuffer()) };
}

/** Writes every recipe's text (and photo) into the ZIP one after the other and hands it to the browser. A recipe that
 * fails is named at the end; the others still come. The amounts store is put back, as the book page does not own it. */
async function run() {
  running.value = true;
  finished.value = false;
  done.value = 0;
  failed.value = [];
  const folder = safeFileName(props.cookbookName);
  const names = uniqueNames(props.recipes.map(recipe => safeFileName(recipe.name ?? "")));
  const before = khAmounts.value;
  const entries: ZipEntry[] = [];
  for (const [index, recipe] of props.recipes.entries()) {
    const path = `${folder}/${names[index]}`;
    try {
      await loadAmounts(recipe);
      const scale = mode.value === "all" && recipe.recipeServings ? (servingsFactor(servings.value, recipe.recipeServings) ?? 1) : 1;
      entries.push({ name: `${path}.txt`, data: new TextEncoder().encode(text(recipe, scale)) });
      const photo = withPhotos.value ? await photoEntry(recipe, path) : null;
      if (photo) entries.push(photo);
    }
    catch {
      failed.value.push(recipe.name ?? "");
    }
    done.value++;
  }
  khAmounts.value = before;
  if (entries.length) saveFile(`${folder}.zip`, makeZip(entries), "application/zip");
  running.value = false;
  finished.value = true;
}
</script>
