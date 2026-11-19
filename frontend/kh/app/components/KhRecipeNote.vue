<!-- KH: the household's note on a recipe (D82), right under the head of the recipe view: a soft box "Unsere Notiz" with
a pencil that turns the text into an editor, or, without a note, a small button to add one. Only people of the
recipe's own group see it, because the note belongs to their household. -->
<template>
  <div v-if="isOwnGroup && text !== undefined" class="kh-note d-print-none px-4 pt-2" data-testid="kh-note">
    <v-form v-if="editing" @submit.prevent="submit">
      <v-textarea
        v-model="draft"
        :label="$t('kh.note.title')"
        :placeholder="$t('kh.note.placeholder')"
        :maxlength="MAX_NOTE_LENGTH"
        counter
        auto-grow
        rows="2"
        variant="outlined"
        autofocus
      />
      <div class="d-flex ga-2 justify-end">
        <v-btn variant="text" :disabled="saving" @click="editing = false">
          {{ $t("general.cancel") }}
        </v-btn>
        <v-btn type="submit" color="primary" :loading="saving">
          {{ $t("general.save") }}
        </v-btn>
      </div>
    </v-form>

    <v-sheet v-else-if="text" color="primary" class="kh-note-box rounded-lg pa-3 d-flex align-start ga-2">
      <div class="flex-grow-1">
        <div class="text-subtitle-2 font-weight-bold">
          {{ $t("kh.note.title") }}
        </div>
        <p class="kh-note-text mb-0">
          {{ text }}
        </p>
      </div>
      <v-btn icon variant="text" size="small" :aria-label="$t('kh.note.edit')" @click="edit">
        <v-icon :icon="$globals.icons.edit" />
      </v-btn>
    </v-sheet>

    <v-btn v-else variant="text" size="small" :prepend-icon="$globals.icons.createAlt" @click="edit">
      {{ $t("kh.note.add") }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useKhNote } from "../composables/use-kh-note";
import { useLoggedInState } from "~/composables/use-logged-in-state";

const props = defineProps<{ recipeId: string }>();

const MAX_NOTE_LENGTH = 2000; // as the server (mealie/kh/notes/schemas.py)

const { isOwnGroup } = useLoggedInState();
const { text, load, save } = useKhNote(() => props.recipeId);
const editing = ref(false);
const draft = ref("");
const saving = ref(false);

onMounted(() => {
  if (isOwnGroup.value) void load();
});

function edit() {
  draft.value = text.value ?? "";
  editing.value = true;
}

async function submit() {
  saving.value = true;
  if (await save(draft.value)) editing.value = false;
  saving.value = false;
}
</script>

<style scoped>
/* a soft tint of the main color; the text keeps the normal color, so it reads in the light and the dark theme */
.kh-note-box {
  background: rgba(var(--v-theme-primary), 0.12) !important;
  color: rgb(var(--v-theme-on-surface)) !important;
}
.kh-note-text {
  white-space: pre-wrap;
}
</style>
