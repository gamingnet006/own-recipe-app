<!-- KH: "Suggest tags" for recipes that have none: proposals from the rules (and, on request, the AI) with a checkbox
per tag; only what the person confirms is saved, nothing is tagged silently. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.tag-suggest.title") }}
      </template>
      {{ $t("kh.tag-suggest.description") }}
    </BasePageTitle>

    <div class="d-flex flex-wrap ga-2 mb-4">
      <v-btn color="primary" :loading="loading" @click="search(false)">
        {{ $t("kh.tag-suggest.search") }}
      </v-btn>
      <v-btn v-if="result?.aiAvailable && result.aiLeft" variant="outlined" :loading="loading" @click="search(true)">
        {{ $t("kh.tag-suggest.search-ai") }}
      </v-btn>
      <v-btn v-if="asked.length" variant="text" @click="askAgain">
        {{ $t("kh.tag-suggest.ask-again") }}
      </v-btn>
    </div>

    <v-alert v-if="failed" type="error" variant="tonal" class="mb-4">
      {{ $t("kh.tag-suggest.failed") }}
    </v-alert>
    <p v-else-if="result && !result.proposals.length" class="text-center text-medium-emphasis py-8">
      {{ $t("kh.tag-suggest.none") }}
    </p>

    <template v-if="result?.proposals.length">
      <p class="text-body-2 text-medium-emphasis mb-2">
        {{ $t("kh.tag-suggest.left", { n: result.withoutProposal }) }}
      </p>
      <v-card v-for="proposal in result.proposals" :key="proposal.recipeId" variant="outlined" class="pa-4 mb-3">
        <NuxtLink :to="`/g/${groupSlug}/r/${proposal.slug}`" class="text-body-1 font-weight-medium">
          {{ proposal.name }}
        </NuxtLink>
        <v-checkbox
          v-for="tag in proposal.tags"
          :key="tag.id"
          :model-value="!unticked.has(`${proposal.recipeId}:${tag.id}`)"
          :label="tag.name"
          density="compact"
          hide-details
          @update:model-value="toggle(proposal.recipeId, tag.id)"
        />
      </v-card>
      <v-btn color="success" :loading="saving" :disabled="!items.length" @click="save">
        {{ $t("kh.tag-suggest.apply", { n: items.length }) }}
      </v-btn>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import type { KhTagSuggestions } from "../../../lib/api/tags";
import { KhTagsApi } from "../../../lib/api/tags";
import { clearAsked, loadAsked, saveAsked } from "../../../lib/asked-tags";
import { confirmedItems } from "../../../lib/draft-tags";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const groupSlug = useRoute().params.groupSlug as string;
const api = new KhTagsApi(useRequests());

const result = ref<KhTagSuggestions | null>(null);
const asked = ref<string[]>(loadAsked(groupSlug)); // recipes the AI was asked about, kept in this browser; not asked again
const unticked = ref(new Set<string>()); // "recipeId:tagId" of the tags a person took away
const loading = ref(false);
const saving = ref(false);
const failed = ref(false);
const items = computed(() => confirmedItems(result.value?.proposals ?? [], unticked.value));

useSeoMeta({ title: () => i18n.t("kh.tag-suggest.title") });

/** Looks for proposals again; USEAI also asks the AI about a few recipes the rules found nothing for. */
async function search(useAi: boolean) {
  loading.value = true;
  const { data } = await api.suggest(useAi, asked.value);
  loading.value = false;
  failed.value = !data;
  if (data) {
    result.value = data;
    asked.value = [...asked.value, ...data.askedIds];
    saveAsked(groupSlug, asked.value);
    unticked.value = new Set();
  }
}

/** Forgets which recipes were asked, so the AI may look at them again. */
function askAgain() {
  clearAsked(groupSlug);
  asked.value = [];
}

function toggle(recipeId: string, tagId: string) {
  const key = `${recipeId}:${tagId}`;
  const next = new Set(unticked.value);
  if (!next.delete(key)) next.add(key);
  unticked.value = next;
}

/** Saves the ticked tags and looks again, so the saved recipes leave the list. */
async function save() {
  saving.value = true;
  const { error } = await api.apply(items.value);
  saving.value = false;
  if (error) alert.error(i18n.t("kh.tag-suggest.failed"));
  else await search(false);
}
</script>
