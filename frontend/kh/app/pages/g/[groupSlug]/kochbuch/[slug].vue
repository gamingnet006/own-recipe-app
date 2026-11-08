<!-- KH: the book of a cookbook (D43): Mealie's cookbook with its recipes in the editor and the live preview, ready
to print. The settings belong to the cookbook and are saved by themselves. -->
<template>
  <v-container>
    <h1 class="text-h5 mb-4 d-print-none">
      {{ $t("kh.book.page-title") }}
    </h1>
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

const loading = ref(true);
const book = ref<Awaited<ReturnType<typeof loadCookbookBook>>>(null);

/** Loads the book; also the retry after an error. The editor is mounted anew, so its saving starts from what was read. */
async function load() {
  loading.value = true;
  book.value = await loadCookbookBook(route.params.slug as string, auth.user.value?.householdId);
  loading.value = false;
}

onMounted(load);
</script>
