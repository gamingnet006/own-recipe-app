<!-- KH: the tags of a recipe in the draft review (wave 2): the suggested ones as chips that can be removed, and
"Add tag" choosing from the group's tags. A new tag stays possible but is made on purpose, in its own dialog. -->
<template>
  <div>
    <h3 class="text-h6 mb-1">
      {{ $t("kh.drafts.tags.title") }}
    </h3>
    <p class="text-body-2 text-medium-emphasis mb-3">
      {{ $t("kh.drafts.tags.hint") }}
    </p>
    <v-autocomplete
      v-model="tagIds"
      :items="tagItems"
      item-title="name"
      item-value="id"
      :label="$t('kh.drafts.tags.add')"
      multiple
      chips
      closable-chips
      variant="outlined"
      hide-details
    />
    <BaseDialog
      v-model="creating.open"
      keep-open
      :loading="creating.busy"
      :title="$t('kh.drafts.tags.new')"
      :icon="$globals.icons.tags"
      can-submit
      :submit-text="$t('kh.drafts.where.create')"
      :submit-disabled="!creating.name.trim()"
      @submit="create"
    >
      <v-card-text>
        <v-text-field v-model="creating.name" :label="$t('kh.drafts.where.name')" autofocus variant="outlined" />
      </v-card-text>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { useTagStore } from "~/composables/store/use-tag-store";
import { alert } from "~/composables/use-toast";
import type { TagOut } from "~/lib/api/types/recipe";
import type { KhTagRef } from "../lib/api/tags";
import { findByName } from "../lib/draft-edit";
import { withTag } from "../lib/draft-tags";

const NEW = "__new__"; // the list's last entry, which asks for a name instead of picking a tag

// the tags the recipe keeps; they start as the recognized ones
const chosen = defineModel<KhTagRef[]>({ required: true });

const i18n = useI18n();
const { $globals } = useNuxtApp();
const { store: tags, actions } = useTagStore();
const creating = reactive({ open: false, busy: false, name: "" });
// making a tag needs the right to organize, like Mealie's own tag page
const canOrganize = computed(() => !!useMealieAuth().user.value?.canOrganize);

const tagItems = computed(() => [
  ...tags.value,
  ...(canOrganize.value ? [{ id: NEW, name: i18n.t("kh.drafts.tags.new") }] : []),
]);

const tagIds = computed({
  get: () => chosen.value.map(tag => tag.id),
  set: (ids: string[]) => {
    if (ids.includes(NEW)) {
      Object.assign(creating, { open: true, name: "" });
      return;
    }
    chosen.value = ids.flatMap(id => tags.value.filter(tag => tag.id === id).map(toRef));
  },
});

function toRef(tag: TagOut): KhTagRef {
  return { id: tag.id, name: tag.name, slug: tag.slug };
}

/** Makes the tag the dialog asked for (a tag of that name that exists is reused) and keeps the dialog open when
 * that fails. */
async function create() {
  const name = creating.name.trim();
  if (!name || creating.busy) return;
  creating.busy = true;
  try {
    const tag = findByName(tags.value, name) ?? (await actions.createOne({ name } as TagOut));
    if (!tag) {
      alert.error(i18n.t("kh.drafts.where.create-failed"));
      return;
    }
    chosen.value = withTag(chosen.value, toRef(tag));
    creating.open = false;
  }
  finally {
    creating.busy = false;
  }
}
</script>
