<template>
  <v-container>
    <!-- KH: tags for recipes that have none, proposed and applied only after confirmation -->
    <v-btn :to="`/g/${$route.params.groupSlug}/schlagworte`" variant="outlined" class="mb-4">
      {{ $t("kh.tag-suggest.title") }}
    </v-btn>
    <RecipeOrganizerPage
      v-if="store"
      :items="store"
      :icon="$globals.icons.tags"
      item-type="tags"
      @delete="actions.deleteOne"
      @update="actions.updateOne"
    >
      <template #title>
        {{ $t("tag.tags") }}
      </template>
    </RecipeOrganizerPage>
  </v-container>
</template>

<script setup lang="ts">
import RecipeOrganizerPage from "~/components/Domain/Recipe/RecipeOrganizerPage.vue";
import { useTagStore } from "~/composables/store";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const { store, actions } = useTagStore();
const i18n = useI18n();

useSeoMeta({
  title: i18n.t("tag.tags"),
});
</script>
