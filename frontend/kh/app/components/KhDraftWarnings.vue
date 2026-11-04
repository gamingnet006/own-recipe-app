<!-- KH: the hints on a draft: possible duplicates (phase 2), each linking to the recipe or the other draft it may
repeat, and what looks wrong in it (D39), as text. Names come from recipes and drafts, so they are shown as text only. -->
<template>
  <v-alert type="warning" variant="tonal" density="compact">
    <div v-for="(warning, index) in warnings" :key="index">
      <i18n-t :keypath="`kh.drafts.warning.${warning.kind}`" tag="span">
        <template #name>
          <NuxtLink v-if="warningTarget(warning, groupSlug)" :to="warningTarget(warning, groupSlug)">
            {{ warning.name || $t("kh.drafts.another-draft") }}
          </NuxtLink>
          <span v-else>{{ warning.name }}</span>
        </template>
      </i18n-t>
    </div>
  </v-alert>
</template>

<script setup lang="ts">
import type { KhDraftWarning } from "../lib/api/drafts";
import { warningTarget } from "../composables/use-kh-drafts";

defineProps<{ warnings: KhDraftWarning[] }>();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string);
</script>
