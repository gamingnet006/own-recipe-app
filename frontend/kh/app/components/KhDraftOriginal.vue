<!-- KH: what a draft was made from (phase 2): its photos, its text or its link. The text is shown as plain
text, and only an http(s) link becomes clickable, so nothing handed in can run in the page. -->
<template>
  <div v-if="draft.sourceType === 'image'" class="d-flex flex-column ga-2">
    <a
      v-for="n in draft.originalFiles.length"
      :key="n"
      :href="api.originalUrl(draft.id, n)"
      target="_blank"
      rel="noopener"
    >
      <v-img :src="api.originalUrl(draft.id, n)" rounded />
    </a>
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
import { useKhDraftsApi } from "../composables/use-kh-drafts";
import { validators } from "~/composables/use-validators";

const props = defineProps<{ draft: KhDraft }>();

const api = useKhDraftsApi();
const webLink = computed(() => validators.url(props.draft.sourceUrl) === true);
</script>

<style scoped>
.kh-source-text {
  white-space: pre-wrap;
}
</style>
