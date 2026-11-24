<!-- KH: the review of one draft (phase 2): hints on possible duplicates, the original next to what was
recognized (one below the other on a phone, side by side from iPad width), then save, save and edit, or discard. -->
<template>
  <v-container class="lg-container">
    <v-alert v-if="loadError && !missing" type="error" variant="tonal" class="mb-4">
      {{ errorText(loadError, i18n.t) }}
    </v-alert>
    <p v-if="missing" class="text-center py-8">
      {{ $t("kh.drafts.error.not_found") }}
    </p>
    <template v-else-if="draft">
      <BasePageTitle divider>
        <template #title>
          {{ draftTitle(draft) || $t(`kh.drafts.source.${draft.sourceType}`) }}
        </template>
        {{ $t(`kh.drafts.status.${draft.status}`) }}
      </BasePageTitle>

      <KhDraftWarnings v-if="draft.status === 'ready' && draft.warnings.length" :warnings="draft.warnings" class="mb-4" />
      <v-alert v-if="draft.status === 'failed'" type="error" variant="tonal" class="mb-4">
        {{ errorText(draft.error ?? "unknown", i18n.t, canManage) }}
        <template #append>
          <!-- without an AI provider trying again cannot help: typing the recipe by hand can (D76) -->
          <v-btn v-if="draft.error === NO_AI_ERROR" variant="text" :to="`/g/${groupSlug}/r/create/new`">
            {{ $t("kh.drafts.type-yourself-short") }}
          </v-btn>
          <v-btn variant="text" @click="retry">
            {{ $t("kh.drafts.retry") }}
          </v-btn>
        </template>
      </v-alert>

      <v-row>
        <v-col :cols="columns">
          <h2 class="text-h6 mb-2">
            {{ $t("kh.drafts.original") }}
          </h2>
          <KhDraftOriginal :draft="draft" @reordered="draft = $event" />
        </v-col>
        <v-col :cols="columns">
          <h2 class="text-h6 mb-2">
            {{ $t("kh.drafts.result") }}
          </h2>
          <p v-if="draft.status === 'working'">
            {{ $t("kh.drafts.working-hint") }}
          </p>
          <KhDraftReview
            v-else-if="draft.recipe"
            v-model:linked="linkedSteps"
            :recipe="{ ...draft.recipe, ...changes }"
            :editable="draft.status === 'ready'"
            :edit="edit"
          />
          <!-- D76: "Ergibt 12 Muffins"; the number is saved as servings and yield amount, the text as yield text -->
          <div v-if="draft.status === 'ready' && changes" class="d-flex align-center ga-3 mt-2">
            <span class="text-body-1">{{ $t("kh.drafts.yield") }}</span>
            <v-number-input
              v-model="yieldAmount"
              :min="0"
              :precision="null"
              density="compact"
              hide-details
              variant="underlined"
              control-variant="hidden"
              :aria-label="$t('recipe.servings')"
              style="max-width: 5rem"
            />
            <v-text-field
              v-model="changes.recipeYield"
              density="compact"
              hide-details
              variant="underlined"
              :aria-label="$t('recipe.yield-text')"
            />
          </div>
        </v-col>
      </v-row>

      <KhDraftWhere v-if="draft.status === 'ready' && changes" v-model="categories" class="mt-6" />

      <!-- D76: the buttons to accept stay at the bottom of the screen above the bar, so a long recipe needs no scrolling -->
      <div v-if="draft.status === 'ready'" class="kh-actions d-flex ga-2 mt-6">
        <v-btn color="success" :loading="busy || editing > 0" @click="approve(false)">
          {{ $t("kh.drafts.approve") }}
        </v-btn>
        <v-btn color="primary" variant="tonal" :loading="busy || editing > 0" @click="approve(true)">
          {{ $t("kh.drafts.approve-and-edit") }}
        </v-btn>
      </div>
      <div v-if="draft.status === 'ready' || draft.status === 'failed'" class="d-flex mt-2">
        <v-spacer />
        <v-btn color="error" variant="text" :prepend-icon="$globals.icons.delete" @click="discarding = true">
          {{ $t("kh.drafts.discard") }}
        </v-btn>
      </div>
    </template>

    <BaseDialog
      v-model="discarding"
      :title="$t('kh.drafts.discard')"
      :icon="$globals.icons.alertCircle"
      color="error"
      can-confirm
      @confirm="discard"
    >
      <v-card-text>
        {{ $t("kh.drafts.discard-confirm") }}
      </v-card-text>
    </BaseDialog>
    <BaseDialog
      v-model="duplicates.open"
      :title="$t('kh.drafts.duplicates-title')"
      :icon="$globals.icons.alertCircle"
      color="warning"
      can-submit
      :submit-text="$t('kh.drafts.approve-anyway')"
      @submit="approve(duplicates.edit, true)"
    >
      <v-card-text>
        <KhDraftWarnings :warnings="duplicates.warnings" />
      </v-card-text>
      <template #custom-card-action>
        <v-btn color="error" variant="text" @click="discardFromDuplicates">
          {{ $t("kh.drafts.discard-this") }}
        </v-btn>
      </template>
    </BaseDialog>
  </v-container>
</template>

<script setup lang="ts">
import type { KhCategoryRef, KhDraft, KhDraftWarning, KhRecipeChanges } from "~~/kh/app/lib/api/drafts";
import { remapLinked, type KhDraftEdit } from "~~/kh/app/lib/draft-edit";
import {
  approveTarget,
  draftTitle,
  errorText,
  draftAmounts,
  NO_AI_ERROR,
  pollingNeeded,
  recipeChanges,
  requestError,
  reviewLayout,
  setYieldNumber,
  useKhDraftsApi,
  useKhPolling,
  yieldNumber,
} from "~~/kh/app/composables/use-kh-drafts";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const router = useRouter();
const display = useDisplay();
const api = useKhDraftsApi();

const id = route.params.id as string;
const groupSlug = route.params.groupSlug as string;
const draft = ref<KhDraft | null>(null);
const missing = ref(false);
const loadError = ref<string | null>(null);
const busy = ref(false);
const discarding = ref(false);
const duplicates = reactive({ open: false, edit: false, warnings: [] as KhDraftWarning[] });
const changes = ref<KhRecipeChanges | null>(null);
// the step links the review keeps (D39); only a ready draft can change them
const linkedSteps = computed({
  get: () => changes.value?.linkedSteps,
  set: (value) => {
    if (changes.value && value) changes.value.linkedSteps = value;
  },
});
const categories = computed({
  get: () => changes.value?.recipeCategory ?? [],
  set: (value: KhCategoryRef[]) => {
    if (changes.value) changes.value.recipeCategory = value;
  },
});
const yieldAmount = computed({
  get: () => (changes.value ? yieldNumber(changes.value) : 0),
  set: (value: number | null) => {
    if (changes.value) setYieldNumber(changes.value, value ?? 0);
  },
});
const canManage = !!useMealieAuth().user.value?.canManage;
const columns = computed(() => (reviewLayout(display.width.value) === "side" ? 6 : 12));

useSeoMeta({ title: () => (draft.value ? draftTitle(draft.value) : i18n.t("kh.drafts.drafts")) });

const { reload } = useKhPolling(async () => {
  const { data, error } = await api.get(id);
  if (data) draft.value = data;
  if (data?.status === "ready" && !changes.value) changes.value = recipeChanges(data.recipe);
  loadError.value = data ? null : requestError(error).code;
  missing.value = loadError.value === "not_found"; // anything else keeps what is shown and looks again
  return (!!loadError.value && !missing.value) || (!!draft.value && pollingNeeded([draft.value]));
});

function showError(error: unknown) {
  alert.error(errorText(requestError(error).code, i18n.t, canManage));
}

// edits go one after the other, so the answers come back in order and the newest one is what stays on the page
let pending: Promise<unknown> = Promise.resolve();
const editing = ref(0);

/** Sends one change made in the preview, after the ones before it; true when it worked. */
function edit(body: KhDraftEdit): Promise<boolean> {
  editing.value++;
  const result = pending.then(() => send(body));
  pending = result.finally(() => { editing.value--; });
  return result;
}

/** Shows the draft as the server has it after the edit; the step links the review kept follow their links to their
 * new places. A failure shows its message and keeps what the page had. */
async function send(body: KhDraftEdit): Promise<boolean> {
  const { data, error } = await api.edit(id, body);
  if (!data) {
    showError(error);
    return false;
  }
  if (changes.value) {
    changes.value.linkedSteps = remapLinked(
      draftAmounts(draft.value?.recipe).stepAmounts,
      draftAmounts(data.recipe).stepAmounts,
      changes.value.linkedSteps,
    );
  }
  draft.value = data;
  return true;
}

/** Saves the draft as a recipe with the review's servings and yield and opens it. Possible duplicates found
 * since the recognition are asked about first; FORCE saves anyway. If someone else was quicker, their recipe opens. */
async function approve(edit: boolean, force = false) {
  busy.value = true;
  await pending; // an edit still on its way is part of what is saved
  const { data, error } = await api.approve(id, force, changes.value ?? undefined);
  busy.value = false;
  if (data) {
    router.push(approveTarget(data.slug, groupSlug, edit));
    return;
  }
  const answer = requestError(error);
  if (answer.code === "duplicates") {
    Object.assign(duplicates, { open: true, edit, warnings: answer.warnings ?? [] });
  }
  else if (answer.code === "already_approved" && answer.slug) {
    router.push(approveTarget(answer.slug, groupSlug, false));
  }
  else {
    showError(error);
  }
}

async function retry() {
  const { error } = await api.retry(id);
  if (error) showError(error);
  await reload();
}

/** The duplicate hint is not worth a recipe: close it and ask whether to discard the draft. */
function discardFromDuplicates() {
  duplicates.open = false;
  discarding.value = true;
}

async function discard() {
  const { error } = await api.discard(id);
  if (error) {
    showError(error);
    return;
  }
  router.push(`/g/${groupSlug}/drafts`);
}
</script>

<style scoped>
/* above the bar of the bottom navigation (Vuetify's layout variable), on wide screens above the screen's edge */
.kh-actions {
  position: sticky;
  bottom: var(--v-layout-bottom, 0px);
  z-index: 5;
  padding: 8px 0;
  background: rgb(var(--v-theme-background));
  border-top: 1px solid rgb(var(--v-theme-surface-variant), 0.2);
}
@media (min-width: 840px) {
  .kh-actions {
    padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
