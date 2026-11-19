<!-- KH: the household's note as a small banner above the step in cook mode (D82); a tap folds it to one line, and that
choice is kept for the browser session (storage that is blocked just means it opens again). -->
<template>
  <div v-if="isOwnGroup && text" class="kh-cook-note rounded-lg px-3 py-1 mb-2" data-testid="kh-cook-note">
    <button
      type="button"
      class="d-flex align-center ga-2 w-100 text-left py-1"
      :aria-expanded="!folded"
      @click="folded = !folded"
    >
      <v-icon :icon="$globals.icons.noteTextOutline" size="small" />
      <span class="text-subtitle-2 font-weight-bold flex-grow-1">{{ $t("kh.note.title") }}</span>
      <v-icon :icon="$globals.icons.chevronDown" size="small" :class="{ 'kh-open': !folded }" />
    </button>
    <p v-show="!folded" class="kh-cook-note-text text-body-2 pb-1 mb-0">
      {{ text }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useSessionStorage } from "@vueuse/core";
import { useKhNote } from "../composables/use-kh-note";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const props = defineProps<{ recipeId: string }>();

const { isOwnGroup } = useLoggedInState();
const { text, load } = useKhNote(() => props.recipeId);
const folded = useSessionStorage("kh-cook-note-folded", false);

onMounted(() => {
  if (isOwnGroup.value) void load();
});
</script>

<style scoped>
.kh-cook-note {
  background: rgba(var(--v-theme-primary), 0.12);
}
.kh-open {
  transform: rotate(180deg);
}
.kh-cook-note-text {
  white-space: pre-wrap;
}
</style>
