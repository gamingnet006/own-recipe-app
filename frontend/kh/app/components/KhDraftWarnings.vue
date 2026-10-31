<!-- KH: the hints on possible duplicates of a draft (phase 2), each linking to the recipe or the other draft it
may repeat. Names come from recipes and drafts, so they are shown as text only. -->
<template>
  <v-alert type="warning" variant="tonal" density="compact">
    <div v-for="(warning, index) in warnings" :key="index">
      <i18n-t :keypath="`kh.drafts.warning.${warning.kind}`" tag="span">
        <template #name>
          <NuxtLink :to="warningTarget(warning, groupSlug)">
            {{ warning.name || $t("kh.drafts.another-draft") }}
          </NuxtLink>
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
