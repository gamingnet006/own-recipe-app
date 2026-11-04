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
        {{ errorText(draft.error ?? "unknown", i18n.t) }}
        <template #append>
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
          <KhDraftOriginal :draft="draft" />
        </v-col>
        <v-col :cols="columns">
          <h2 class="text-h6 mb-2">
            {{ $t("kh.drafts.result") }}
          </h2>
          <p v-if="draft.status === 'working'">
            {{ $t("kh.drafts.working-hint") }}
          </p>
          <KhDraftReview v-else-if="draft.recipe" v-model:linked="linkedSteps" :recipe="{ ...draft.recipe, ...changes }" />
          <!-- Like Mealie's editor: servings, yield amount and yield text, saved with the recipe -->
          <v-row v-if="draft.status === 'ready' && changes" dense class="mt-2">
            <v-col cols="3">
              <v-number-input
                v-model="changes.recipeServings"
                :min="0"
                :precision="null"
                density="compact"
                :label="$t('recipe.servings')"
                variant="underlined"
                control-variant="hidden"
              />
            </v-col>
            <v-col cols="3">
              <v-number-input
                v-model="changes.recipeYieldQuantity"
                :min="0"
                :precision="null"
                density="compact"
                :label="$t('recipe.yield')"
                variant="underlined"
                control-variant="hidden"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="changes.recipeYield"
                density="compact"
                :label="$t('recipe.yield-text')"
                variant="underlined"
              />
            </v-col>
          </v-row>
        </v-col>
      </v-row>

      <div v-if="draft.status === 'ready' || draft.status === 'failed'" class="d-flex flex-wrap ga-2 mt-6">
        <template v-if="draft.status === 'ready'">
          <v-btn color="success" :loading="busy" @click="approve(false)">
            {{ $t("kh.drafts.approve") }}
          </v-btn>
          <v-btn color="primary" variant="tonal" :loading="busy" @click="approve(true)">
            {{ $t("kh.drafts.approve-and-edit") }}
          </v-btn>
        </template>
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
    </BaseDialog>
  </v-container>
</template>

<script setup lang="ts">
import type { KhDraft, KhDraftWarning, KhRecipeChanges } from "~~/kh/app/lib/api/drafts";
import {
  approveTarget,
  draftTitle,
  errorText,
  pollingNeeded,
  recipeChanges,
  requestError,
  reviewLayout,
  useKhDraftsApi,
  useKhPolling,
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
  alert.error(errorText(requestError(error).code, i18n.t));
}

/** Saves the draft as a recipe with the review's servings and yield and opens it. Possible duplicates found
 * since the recognition are asked about first; FORCE saves anyway. If someone else was quicker, their recipe opens. */
async function approve(edit: boolean, force = false) {
  busy.value = true;
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

async function discard() {
  const { error } = await api.discard(id);
  if (error) {
    showError(error);
    return;
  }
  router.push(`/g/${groupSlug}/drafts`);
}
</script>
