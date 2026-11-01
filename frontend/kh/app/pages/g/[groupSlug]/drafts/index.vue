<!-- KH: the intake (D38): the form for a new recipe, and below it the household's drafts that are not saved yet
(phase 2), newest first. The list looks again by itself while one is being recognized, and a failed one can be
tried again. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.intake") }}
      </template>
      {{ $t("kh.drafts.intake-description") }}
    </BasePageTitle>
    <KhDraftIntake :shared-link="sharedLink" @submitted="onSubmitted" />
    <p class="text-body-2 text-medium-emphasis mt-4 mb-8">
      {{ $t("kh.drafts.shortcut-hint") }}
      <NuxtLink :to="`/g/${groupSlug}/r/create/new`">
        {{ $t("kh.drafts.type-yourself") }}
      </NuxtLink>
    </p>
    <h2 class="text-h6 mb-2">
      {{ $t("kh.drafts.drafts") }}
    </h2>
    <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
      {{ errorText(loadError, i18n.t) }}
    </v-alert>
    <p v-else-if="loaded && !drafts.length" class="text-center text-medium-emphasis py-8">
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
  useKhDraftCount,
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

useSeoMeta({ title: i18n.t("kh.nav.intake") });

const { refresh: refreshCount } = useKhDraftCount();
const groupSlug = computed(() => route.params.groupSlug as string);
// A link shared to the app arrives through Mealie's import page, which leads here with this query
const sharedLink = typeof route.query.recipe_import_url === "string" ? route.query.recipe_import_url : "";
const drafts = ref<KhDraft[]>([]);
const loaded = ref(false);
const loadError = ref<string | null>(null);
const sourceIcons = { link: $globals.icons.link, text: $globals.icons.textBox, image: $globals.icons.fileImage };

const { reload } = useKhPolling(async () => {
  const { data, error } = await api.list();
  if (data) drafts.value = data;
  loadError.value = data ? null : requestError(error).code;
  loaded.value = true;
  return pollingNeeded(drafts.value) || !!loadError.value; // after a failed load, look again until it works
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

/** A new draft shows in the list right away, and the number in the menu follows. */
async function onSubmitted() {
  await Promise.all([reload(), refreshCount()]);
}

async function retry(draft: KhDraft) {
  const { error } = await api.retry(draft.id);
  if (error) alert.error(errorText(requestError(error).code, i18n.t));
  await reload();
}
</script>
