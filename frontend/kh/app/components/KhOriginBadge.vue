<!-- KH: shows on a recipe where it came from (phase 2), e.g. "From a photo · 31.10.2026 · Alex", with the way
back to the original; recipes without a draft, older or typed in, show nothing. -->
<template>
  <div v-if="origin" class="d-flex flex-wrap align-center ga-2 px-4 pt-3">
    <v-chip size="small" variant="tonal" :prepend-icon="icon">
      {{ label }}
    </v-chip>
    <v-btn size="small" variant="text" :to="`/g/${groupSlug}/drafts/${origin.draftId}`">
      {{ $t("kh.drafts.view-original") }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import type { KhOrigin } from "../lib/api/drafts";
import { originLabel, useKhDraftsApi } from "../composables/use-kh-drafts";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const props = defineProps<{ recipeId: string }>();

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();
const api = useKhDraftsApi();

const origin = ref<KhOrigin | null>(null);
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const label = computed(() => origin.value ? originLabel(origin.value, i18n.t, value => i18n.d(value)) : "");
const icon = computed(() => {
  const icons = { link: $globals.icons.link, text: $globals.icons.textBox, image: $globals.icons.fileImage };
  return origin.value ? icons[origin.value.sourceType] : undefined;
});

// Only the household's own recipes can have an origin; other visitors are not asked for one
watch(() => props.recipeId, async (recipeId) => {
  origin.value = isOwnGroup.value ? (await api.origin(recipeId)).data : null;
}, { immediate: true });
</script>
