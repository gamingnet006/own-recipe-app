<!-- KH: the duplicate report (D43): pairs of recipes that may be the same, most alike first, optionally only those with
one tag (e.g. the tag of a move from another app). Per pair: look at both, keep both (the pair does not come back) or
delete one after a confirmation. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.duplicates") }}
      </template>
      {{ $t("kh.duplicates.description") }}
    </BasePageTitle>

    <v-select
      v-model="tagId"
      :items="tags"
      item-title="name"
      item-value="id"
      :label="$t('kh.duplicates.tag-filter')"
      clearable
      class="mb-4"
    />

    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-else-if="failed" type="error" variant="tonal">
      {{ $t("kh.duplicates.failed") }}
    </v-alert>
    <p v-else-if="!pairs.length" class="text-center text-medium-emphasis py-8">
      {{ $t("kh.duplicates.none") }}
    </p>

    <v-card v-for="pair in pairs" :key="`${pair.a.slug}|${pair.b.slug}`" variant="outlined" class="pa-4 mb-3">
      <p class="text-caption text-medium-emphasis mb-2">
        {{ pairLabel(pair, $t) }}
      </p>
      <div v-for="recipe in [pair.a, pair.b]" :key="recipe.slug" class="mb-2">
        <div class="text-body-1 font-weight-medium">
          {{ recipe.name }}
        </div>
        <div class="text-body-2 text-medium-emphasis">
          {{ originOf(recipe.orgUrl) ?? $t("kh.duplicates.own") }}
        </div>
      </div>
      <div class="d-flex flex-wrap ga-2 mt-3">
        <v-btn variant="tonal" @click="view(pair)">
          {{ $t("kh.duplicates.view") }}
        </v-btn>
        <v-btn variant="tonal" @click="keepBoth(pair)">
          {{ $t("kh.duplicates.keep-both") }}
        </v-btn>
        <v-btn v-for="recipe in [pair.a, pair.b]" :key="recipe.slug" variant="tonal" color="error" @click="toDelete = recipe">
          {{ $t("kh.duplicates.delete", { title: recipe.name }) }}
        </v-btn>
      </div>
    </v-card>

    <v-dialog :model-value="!!toDelete" max-width="480" @update:model-value="toDelete = null">
      <v-card v-if="toDelete" class="pa-4">
        <v-card-text>{{ $t("kh.duplicates.delete-confirm", { title: toDelete.name }) }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="toDelete = null">
            {{ $t("general.cancel") }}
          </v-btn>
          <v-btn color="error" @click="confirmDelete">
            {{ $t("general.delete") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { KhBooksApi, type KhDuplicatePair, type KhRecipeRef } from "~~/kh/app/lib/api/books";
import { originOf, pairLabel } from "~~/kh/app/lib/duplicates";
import { useUserApi } from "~/composables/api";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const route = useRoute();
const api = useUserApi();
const books = new KhBooksApi(useRequests());

const tags = ref<{ id: string; name: string }[]>([]);
const tagId = ref<string | null>(null);
const pairs = ref<KhDuplicatePair[]>([]);
const loading = ref(true);
const failed = ref(false);
const toDelete = ref<KhRecipeRef | null>(null);

/** Looks for pairs again, for the chosen tag. */
async function load() {
  loading.value = true;
  const { data } = await books.getDuplicates(tagId.value ?? undefined);
  failed.value = !data;
  pairs.value = data ?? [];
  loading.value = false;
}

onMounted(async () => {
  tags.value = (await api.tags.getAll(1, -1)).data?.items ?? [];
  await load();
});
watch(tagId, load);

/** Opens both recipes in new tabs. */
function view(pair: KhDuplicatePair) {
  for (const recipe of [pair.a, pair.b]) window.open(`/g/${route.params.groupSlug as string}/r/${recipe.slug}`, "_blank");
}

/** "Keep both": the pair is saved as not a double and leaves the list. */
async function keepBoth(pair: KhDuplicatePair) {
  const { error } = await books.ignoreDuplicate(pair.a.slug, pair.b.slug);
  if (error) alert.error(i18n.t("kh.duplicates.failed"));
  else pairs.value = pairs.value.filter(other => other !== pair);
}

/** Deletes the confirmed recipe through Mealie's own function; every pair it is in leaves the list. */
async function confirmDelete() {
  const recipe = toDelete.value;
  toDelete.value = null;
  if (!recipe) return;
  const { error } = await api.recipes.deleteOne(recipe.slug);
  if (error) alert.error(i18n.t("kh.duplicates.failed"));
  else pairs.value = pairs.value.filter(pair => pair.a.slug !== recipe.slug && pair.b.slug !== recipe.slug);
}
</script>
