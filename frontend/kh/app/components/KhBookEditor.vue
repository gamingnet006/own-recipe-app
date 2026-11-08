<!-- KH: the editor of the family cookbook (D43): the switches and the recipe list on the left (above on a phone), the
live preview, which is the printout itself, on the right. In "book" mode the settings are saved by themselves; in
"recipe" mode (the recipe card) nothing is saved. -->
<template>
  <div class="kh-editor">
    <div class="kh-controls d-print-none">
      <v-alert v-if="forbidden" type="info" variant="tonal" class="mb-4">
        {{ $t("kh.book.forbidden") }}
      </v-alert>
      <v-alert v-else-if="status === 'error'" type="error" variant="tonal" class="mb-4">
        {{ $t("kh.book.save-failed") }}
        <template #append>
          <v-btn variant="text" @click="retry">
            {{ $t("kh.book.retry") }}
          </v-btn>
        </template>
      </v-alert>

      <v-btn
        color="primary"
        block
        size="large"
        class="mb-4"
        :disabled="state.empty || !state.entries.length"
        @click="print"
      >
        {{ $t("kh.book.print") }}
      </v-btn>

      <template v-if="mode === 'book'">
        <v-text-field v-model="settings.title" :label="$t('kh.book.title')" :maxlength="BOOK_TEXT_MAX" counter />
        <v-text-field v-model="settings.subtitle" :label="$t('kh.book.subtitle')" :maxlength="BOOK_TEXT_MAX" counter />
        <v-switch v-model="settings.titlePage" color="primary" :label="$t('kh.book.title-page')" hide-details />
        <v-switch v-model="settings.toc" color="primary" :label="$t('kh.book.toc')" hide-details />
        <v-select
          v-model="settings.order"
          :items="orders"
          :label="$t('kh.book.order')"
          class="mt-2"
        />
      </template>

      <h2 class="text-subtitle-1 font-weight-bold mt-2">
        {{ $t("kh.book.all-recipes") }}
      </h2>
      <v-switch v-model="settings.description" color="primary" :label="$t('recipe.description')" hide-details />
      <v-switch v-model="settings.notes" color="primary" :label="$t('recipe.notes')" hide-details />
      <v-switch v-model="settings.oven" color="primary" :label="$t('kh.book.oven')" hide-details />

      <h2 class="text-subtitle-1 font-weight-bold mt-4">
        {{ $t("kh.book.recipes") }}
      </h2>
      <v-card v-for="recipe in recipes" :key="recipe.id" variant="outlined" class="pa-3 mb-2">
        <div class="d-flex align-center ga-3">
          <v-avatar rounded="lg" size="48" color="surface-variant">
            <v-img v-if="recipe.image" :src="recipeTinyImage(recipe.id, recipe.image)" cover />
          </v-avatar>
          <div class="text-body-1 font-weight-medium">
            {{ recipe.name }}
          </div>
        </div>
        <v-switch
          v-if="mode === 'book'"
          :model-value="of(recipe).include"
          color="primary"
          :label="$t('kh.book.in-book')"
          hide-details
          @update:model-value="change(recipe, { include: !!$event })"
        />
        <v-switch
          :model-value="of(recipe).photo && ownPhoto(recipe)"
          color="primary"
          :label="$t('kh.book.with-photo')"
          :disabled="!ownPhoto(recipe) || !recipe.image"
          hide-details
          @update:model-value="change(recipe, { photo: !!$event })"
        />
        <v-switch
          :model-value="ownPhoto(recipe)"
          color="primary"
          :label="$t('kh.book.own-photo')"
          :hint="$t('kh.book.own-photo-hint')"
          persistent-hint
          @update:model-value="setOwnPhoto(recipe, !!$event)"
        />
        <v-text-field
          :model-value="of(recipe).servings ?? ''"
          type="number"
          min="1"
          :label="$t('kh.book.servings')"
          :placeholder="String(recipe.recipeServings ?? '')"
          class="mt-2"
          hide-details
          @update:model-value="change(recipe, { servings: servingsOf($event) })"
        />
      </v-card>
    </div>

    <div class="kh-preview-column">
      <v-alert v-if="state.empty" type="info" variant="tonal" class="d-print-none">
        {{ $t("kh.book.empty") }}
      </v-alert>
      <KhPrintBook v-else :settings="settings" :entries="state.entries" :oven="settings.oven ? oven : null" preview />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import KhPrintBook from "./KhPrintBook.vue";
import { useBookSaving } from "../composables/use-kh-book";
import { KhBooksApi, type KhBookRecipeSettings, type KhBookSettings, type KhRecipeFlags } from "../lib/api/books";
import { editorState, recipeSettings, withRecipe } from "../lib/book";
import { useKhOven } from "../lib/oven";
import { useStaticRoutes } from "~/composables/api";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";
import type { Recipe } from "~/lib/api/types/recipe";

/** Longest title or subtitle; the server refuses more (422). */
const BOOK_TEXT_MAX = 120;

const props = defineProps<{
  mode: "book" | "recipe";
  recipes: Recipe[];
  /** Whether this user may change the cookbook's settings (the cookbook of their own household). */
  canSave: boolean;
  /** The cookbook's id for saving; "book" mode only. */
  cookbookId?: string;
}>();
const settings = defineModel<KhBookSettings>("settings", { required: true });
const flags = defineModel<Record<string, KhRecipeFlags>>("flags", { required: true });

const i18n = useI18n();
const { recipeTinyImage } = useStaticRoutes();
const books = new KhBooksApi(useRequests());
const oven = useKhOven();

const { status, retry } = useBookSaving(props.cookbookId ?? "", settings, props.mode === "book" && props.canSave);
const forbidden = computed(() => props.mode === "book" && (!props.canSave || status.value === "forbidden"));

const orders = computed(() => [
  { title: i18n.t("kh.book.order-category"), value: "category" },
  { title: i18n.t("kh.book.order-alpha"), value: "alpha" },
]);
const state = computed(() => editorState(props.recipes, settings.value, flags.value));

const of = (recipe: Recipe): KhBookRecipeSettings => recipeSettings(settings.value, recipe.slug ?? "");
const ownPhoto = (recipe: Recipe): boolean => !!flags.value[recipe.slug ?? ""]?.ownPhoto;

/** Changes one recipe's settings. */
function change(recipe: Recipe, patch: Partial<KhBookRecipeSettings>) {
  settings.value = withRecipe(settings.value, recipe.slug ?? "", patch);
}

/** The servings typed in the field; empty or not a positive number means the recipe's own. */
function servingsOf(value: string | number | null): number | null {
  const servings = Number(value);
  return value !== "" && value !== null && servings > 0 ? servings : null;
}

/** Sets the "photo is ours" flag on the server first; a refusal says so and leaves the switch as it was. */
async function setOwnPhoto(recipe: Recipe, value: boolean) {
  const slug = recipe.slug ?? "";
  const { error } = await books.putFlags(slug, value);
  if (error) {
    alert.error(i18n.t(error.response?.status === 403 ? "kh.book.flag-forbidden" : "kh.book.save-failed"));
    return;
  }
  flags.value = { ...flags.value, [slug]: { ownPhoto: value } };
  if (!value) change(recipe, { photo: false });
}

function print() {
  window.print();
}
</script>

<style scoped>
.kh-editor {
  display: grid;
  gap: 24px;
}

@media (min-width: 840px) {
  .kh-editor {
    grid-template-columns: 360px minmax(0, 1fr);
    align-items: start;
  }
}

@media print {
  .kh-editor {
    display: block;
  }
}
</style>
