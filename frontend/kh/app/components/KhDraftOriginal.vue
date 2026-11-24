<!-- KH: what a draft was made from (phase 2): its photos, its text or its link. The text is shown as plain
text, and only an http(s) link becomes clickable, so nothing handed in can run in the page. -->
<template>
  <div v-if="draft.sourceType === 'image'" class="d-flex flex-column ga-2">
    <p v-if="canOrder" class="text-caption">
      {{ $t("kh.drafts.photo-first-hint") }}
    </p>
    <div v-for="n in draft.originalFiles.length" :key="n">
      <a :href="photoUrl(n)" target="_blank" rel="noopener">
        <v-img :src="photoUrl(n)" :alt="$t('kh.drafts.original-photo', { n })" rounded />
      </a>
      <KhPhotoMove
        v-if="canOrder"
        :index="n - 1"
        :count="draft.originalFiles.length"
        vertical
        class="mt-1"
        @order="order => reorder(order)"
      />
    </div>
  </div>
  <div v-else-if="draft.sourceType === 'text'" class="kh-source-text">
    {{ draft.sourceText }}
  </div>
  <a
    v-else-if="webLink"
    :href="draft.sourceUrl ?? undefined"
    target="_blank"
    rel="noopener noreferrer"
    class="text-break"
  >{{ draft.sourceUrl }}</a>
  <span v-else class="text-break">{{ draft.sourceUrl }}</span>
</template>

<script setup lang="ts">
import type { KhDraft } from "../lib/api/drafts";
import { errorText, requestError, useKhDraftsApi } from "../composables/use-kh-drafts";
import { alert } from "~/composables/use-toast";
import { validators } from "~/composables/use-validators";

const props = defineProps<{ draft: KhDraft }>();
const emit = defineEmits<{ reordered: [draft: KhDraft] }>();

const i18n = useI18n();
const api = useKhDraftsApi();
// only a ready or failed draft's photos can change places (before a retry too); the first one becomes the recipe photo
const canOrder = computed(() => (props.draft.status === "ready" || props.draft.status === "failed") && props.draft.originalFiles.length > 1);
// the stored file's name in the address, so a reordered photo is not shown from the browser's cache
const photoUrl = (n: number) => `${api.originalUrl(props.draft.id, n)}?v=${props.draft.originalFiles[n - 1]}`;

/** Sends the new order of the photos (old positions from 0) and shows the draft as the server has it now. */
async function reorder(order: number[]) {
  const { data, error } = await api.reorderOriginals(props.draft.id, order.map(position => position + 1));
  if (data) emit("reordered", data);
  else alert.error(errorText(requestError(error).code, i18n.t));
}
const webLink = computed(() => validators.url(props.draft.sourceUrl) === true);
</script>

<style scoped>
.kh-source-text {
  white-space: pre-wrap;
}
</style>
