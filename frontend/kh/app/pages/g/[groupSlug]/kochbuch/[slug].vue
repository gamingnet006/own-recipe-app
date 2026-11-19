<!-- KH: the book of a cookbook (D43): Mealie's cookbook with its recipes in the editor and the live preview, ready
to print. The settings belong to the cookbook and are saved by themselves. -->
<template>
  <v-container>
    <div class="d-flex align-center flex-wrap ga-2 mb-4 d-print-none">
      <h1 class="text-h5 flex-grow-1">
        {{ $t("kh.book.page-title") }}
      </h1>
      <!-- D61: the cookbook's recipes as text files in a ZIP -->
      <v-btn v-if="book && book !== 'error'" variant="tonal" :prepend-icon="$globals.icons.zip" @click="exportDialog = true">
        {{ $t("kh.export.book-button") }}
      </v-btn>
    </div>
    <v-progress-linear v-if="loading" indeterminate class="d-print-none" />
    <v-alert v-else-if="!book" type="error" variant="tonal" class="d-print-none">
      {{ $t("kh.book.not-found") }}
    </v-alert>
    <v-alert v-else-if="book === 'error'" type="error" variant="tonal" class="d-print-none">
      {{ $t("kh.book.load-failed") }}
      <template #append>
        <v-btn variant="text" @click="load">
          {{ $t("kh.book.retry") }}
        </v-btn>
      </template>
    </v-alert>
    <template v-else>
      <KhBookExportDialog v-model="exportDialog" :recipes="book.recipes" :cookbook-name="book.cookbook.name" />
      <v-alert v-if="book.failedRecipes" type="warning" variant="tonal" class="mb-4 d-print-none">
        {{ $t("kh.book.recipes-failed", { n: book.failedRecipes }) }}
        <template #append>
          <v-btn variant="text" @click="load">
            {{ $t("kh.book.reload") }}
          </v-btn>
        </template>
      </v-alert>
      <KhBookEditor
        v-model:settings="book.settings"
        v-model:flags="book.flags"
        mode="book"
        :recipes="book.recipes"
        :can-save="book.canSave"
        :cookbook-id="book.cookbook.id"
      />
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { loadCookbookBook } from "~~/kh/app/composables/use-kh-book";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const route = useRoute();
const auth = useMealieAuth();

const { $globals } = useNuxtApp();
const loading = ref(true);
const exportDialog = ref(false);
const book = ref<Awaited<ReturnType<typeof loadCookbookBook>>>(null);

/** Loads the book; also the retry after an error. The editor is mounted anew, so its saving starts from what was read. */
async function load() {
  loading.value = true;
  book.value = await loadCookbookBook(route.params.slug as string, auth.user.value?.householdId);
  loading.value = false;
}

onMounted(load);
</script>
