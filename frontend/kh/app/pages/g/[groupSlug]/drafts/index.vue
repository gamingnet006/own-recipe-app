<!-- KH: the intake (D38): the household's drafts that are not saved yet (phase 2), newest first, and below them the
form for a new recipe, folded away while drafts wait (D76). The list looks again by itself while one is being
recognized, and a failed one can be tried again, or typed by hand when no AI is set up. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.intake") }}
      </template>
      {{ $t("kh.drafts.intake-description") }}
    </BasePageTitle>
    <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
      {{ errorText(loadError, i18n.t, canManage) }}
    </v-alert>
    <template v-if="drafts.length">
      <h2 class="text-h6 mb-2">
        {{ $t("kh.drafts.drafts") }}
      </h2>
      <v-list lines="three" class="mb-4">
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
          <div v-if="draft.status === 'failed'" class="text-error text-body-2 text-wrap">
            {{ errorText(draft.error ?? "unknown", i18n.t, canManage) }}
          </div>
          <template #append>
            <!-- without an AI provider trying again cannot help: typing the recipe by hand can (D76) -->
            <v-btn v-if="draft.error === NO_AI_ERROR" variant="text" :to="typeYourselfPath" @click.stop>
              {{ $t("kh.drafts.type-yourself-short") }}
            </v-btn>
            <v-btn v-if="draft.status === 'failed'" variant="text" @click.stop.prevent="retry(draft)">
              {{ $t("kh.drafts.retry") }}
            </v-btn>
            <v-chip v-else size="small" :color="draft.status === 'ready' ? 'success' : 'info'">
              {{ $t(`kh.drafts.status.${draft.status}`) }}
            </v-chip>
          </template>
        </v-list-item>
      </v-list>
    </template>
    <v-expansion-panels v-model="addPanel" class="mb-4">
      <v-expansion-panel value="add" :title="$t('kh.drafts.add-recipe')">
        <v-expansion-panel-text>
          <KhDraftIntake :shared-link="shared.link" :shared-text="shared.text" @submitted="onSubmitted" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
    <p v-if="loaded && !drafts.length && !loadError" class="text-center text-medium-emphasis mb-4">
      {{ $t("kh.drafts.no-drafts") }}
    </p>
    <p class="text-body-2 text-medium-emphasis mb-8">
      {{ $t("kh.drafts.shortcut-hint") }}
      <NuxtLink :to="SETUP_PATH">
        {{ $t("kh.drafts.shortcut-link") }}
      </NuxtLink>
      ·
      <NuxtLink :to="typeYourselfPath">
        {{ $t("kh.drafts.type-yourself") }}
      </NuxtLink>
    </p>
  </v-container>
</template>

<script setup lang="ts">
import type { KhDraft } from "~~/kh/app/lib/api/drafts";
import {
  draftTitle,
  errorText,
  NO_AI_ERROR,
  pollingNeeded,
  requestError,
  useKhDraftCount,
  useKhDraftsApi,
  useKhPolling,
} from "~~/kh/app/composables/use-kh-drafts";
import { SETUP_PATH } from "~~/kh/app/lib/device-setup";
import { hasSharedImport, readSharedImport } from "~~/kh/app/lib/shared-import";
import { useStaticRoutes } from "~/composables/api";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const router = useRouter();
const api = useKhDraftsApi();
const { recipeSmallImage } = useStaticRoutes();

useSeoMeta({ title: i18n.t("kh.nav.intake") });

const { refresh: refreshCount } = useKhDraftCount();
const groupSlug = computed(() => route.params.groupSlug as string);
const typeYourselfPath = computed(() => `/g/${groupSlug.value}/r/create/new`);
const canManage = !!useMealieAuth().user.value?.canManage;
// A link or text shared to the app arrives through Mealie's import page, which leads here with this query (D57)
const shared = readSharedImport(route.query, useNuxtApp().$khFeatures.draftMaxText);
const drafts = ref<KhDraft[]>([]);
const loaded = ref(false);
const loadError = ref<string | null>(null);
const sourceIcons = { link: $globals.icons.link, text: $globals.icons.textBox, image: $globals.icons.fileImage };

// The form is folded away while drafts wait, open when there are none or something was shared to the app (D76)
const addPanel = ref<string>();
watch(loaded, () => {
  if (!drafts.value.length || shared.link || shared.text) addPanel.value = "add";
}, { once: true });

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
  // the shared link or text is handed in: a reload, or iOS reopening the home-screen app, must not fill it in again
  if (hasSharedImport(route.query)) await router.replace({ query: {} });
  await Promise.all([reload(), refreshCount()]);
}

async function retry(draft: KhDraft) {
  const { error } = await api.retry(draft.id);
  if (error) alert.error(errorText(requestError(error).code, i18n.t));
  await reload();
}
</script>
