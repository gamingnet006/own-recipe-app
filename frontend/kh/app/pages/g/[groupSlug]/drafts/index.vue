<!-- KH: the household's drafts that are not saved yet (phase 2), newest first. The list looks again by itself
while one is being recognized, and a failed one can be tried again. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.drafts.drafts") }}
      </template>
    </BasePageTitle>
    <div class="d-flex justify-end mb-2">
      <v-btn color="primary" :prepend-icon="$globals.icons.createAlt" :to="`/g/${groupSlug}/drafts/new`">
        {{ $t("kh.drafts.add-recipe") }}
      </v-btn>
    </div>
    <p v-if="loaded && !drafts.length" class="text-center text-medium-emphasis py-8">
      {{ $t("kh.drafts.no-drafts") }}
    </p>
    <v-list lines="three">
      <v-list-item v-for="draft in drafts" :key="draft.id" :to="`/g/${groupSlug}/drafts/${draft.id}`">
        <template #prepend>
          <v-avatar rounded size="56" class="mr-2">
            <v-img v-if="preview(draft)" :src="preview(draft)" cover />
            <v-icon v-else :icon="sourceIcons[draft.sourceType]" />
          </v-avatar>
        </template>
        <v-list-item-title>
          {{ draftTitle(draft) || $t(`kh.drafts.source.${draft.sourceType}`) }}
        </v-list-item-title>
        <v-list-item-subtitle>
          {{ byline(draft) }}
        </v-list-item-subtitle>
        <v-list-item-subtitle v-if="draft.status === 'failed'" class="text-error">
          {{ errorText(draft.error ?? "unknown", i18n.t) }}
        </v-list-item-subtitle>
        <template #append>
          <v-btn v-if="draft.status === 'failed'" variant="text" @click.stop.prevent="retry(draft)">
            {{ $t("kh.drafts.retry") }}
          </v-btn>
          <v-chip v-else size="small" :color="draft.status === 'ready' ? 'success' : 'info'">
            {{ $t(`kh.drafts.status.${draft.status}`) }}
          </v-chip>
        </template>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script setup lang="ts">
import type { KhDraft } from "~~/kh/app/lib/api/drafts";
import {
  draftTitle,
  errorText,
  pollingNeeded,
  requestError,
  useKhDraftsApi,
  useKhPolling,
} from "~~/kh/app/composables/use-kh-drafts";
import { useStaticRoutes } from "~/composables/api";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const api = useKhDraftsApi();
const { recipeSmallImage } = useStaticRoutes();

useSeoMeta({ title: i18n.t("kh.drafts.drafts") });

const groupSlug = computed(() => route.params.groupSlug as string);
const drafts = ref<KhDraft[]>([]);
const loaded = ref(false);
const sourceIcons = { link: $globals.icons.link, text: $globals.icons.textBox, image: $globals.icons.fileImage };

const { reload } = useKhPolling(async () => {
  const { data } = await api.list();
  if (data) drafts.value = data;
  loaded.value = true;
  return pollingNeeded(drafts.value);
});

/** The first original photo, else the picture the recognition took from the page. */
function preview(draft: KhDraft): string | undefined {
  if (draft.originalFiles.length) return api.originalUrl(draft.id, 1);
  if (draft.recipe?.id && draft.recipe.image) return recipeSmallImage(draft.recipe.id, draft.recipe.image);
  return undefined;
}

/** Who handed the draft in and when. */
function byline(draft: KhDraft): string {
  const when = i18n.d(new Date(draft.createdAt), { dateStyle: "short", timeStyle: "short" });
  return [draft.userName, when].filter(Boolean).join(" · ");
}

async function retry(draft: KhDraft) {
  const { error } = await api.retry(draft.id);
  if (error) alert.error(errorText(requestError(error).code, i18n.t));
  await reload();
}
</script>
