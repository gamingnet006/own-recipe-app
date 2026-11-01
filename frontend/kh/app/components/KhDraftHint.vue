<!-- KH: the hint above the start page (D38): when drafts wait for a review, it says how many and leads to the
intake. -->
<template>
  <div v-if="isOwnGroup && count" class="px-3 pt-3">
    <v-btn
      block
      variant="flat"
      color="kh-hint"
      :to="`/g/${groupSlug}/drafts`"
      :prepend-icon="$globals.icons.import"
      :append-icon="$globals.icons.chevronRight"
    >
      {{ $t("kh.nav.drafts-waiting", { count }, count) }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { useKhDraftCount } from "../composables/use-kh-drafts";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const route = useRoute();
const { isOwnGroup } = useLoggedInState();
const { count } = useKhDraftCount();

const groupSlug = computed(() => route.params.groupSlug as string);
</script>
