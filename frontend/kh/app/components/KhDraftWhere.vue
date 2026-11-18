<!-- KH: "Where does the recipe go?" in the draft review (D55): pick categories, or a cookbook that holds one category,
or make a new one; leaving it empty changes nothing. A cookbook here is Mealie's filter on one category, so picking
one adds its category, and a new cookbook makes its category first. -->
<template>
  <div>
    <h3 class="text-h6 mb-1">
      {{ $t("kh.drafts.where.title") }}
    </h3>
    <p class="text-body-2 text-medium-emphasis mb-3">
      {{ $t("kh.drafts.where.hint") }}
    </p>
    <v-autocomplete
      v-model="categoryIds"
      :items="categoryItems"
      item-title="name"
      item-value="id"
      :label="$t('kh.drafts.where.categories')"
      multiple
      chips
      closable-chips
      variant="outlined"
      hide-details
      class="mb-3"
    />
    <v-select
      :model-value="cookbookId"
      :items="cookbookItems"
      item-title="title"
      item-value="value"
      :label="$t('kh.drafts.where.cookbook')"
      variant="outlined"
      hide-details
      @update:model-value="pickCookbook"
    />
    <BaseDialog
      v-model="creating.open"
      keep-open
      :loading="creating.busy"
      :title="$t(creating.kind === 'category' ? 'kh.drafts.where.new-category' : 'kh.drafts.where.new-cookbook')"
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
import { useCategoryStore } from "~/composables/store/use-category-store";
import { useCookbookStore } from "~/composables/store/use-cookbook-store";
import { alert } from "~/composables/use-toast";
import type { CookBookCreate } from "~/lib/api/types/cookbook";
import type { CategoryOut } from "~/lib/api/types/recipe";
import type { KhCategoryRef } from "../lib/api/drafts";
import { cookbookFilter, findByName, oneCategoryCookbooks } from "../lib/draft-edit";

const NEW = "__new__"; // the list's last entry, which asks for a name instead of picking something
const NONE = "";

// the categories the recipe goes to; empty: nothing changes
const chosen = defineModel<KhCategoryRef[]>({ required: true });

const i18n = useI18n();
const { $globals } = useNuxtApp();
const { store: categories, actions: categoryActions } = useCategoryStore();
const { store: cookbooks, actions: cookbookActions } = useCookbookStore();

const cookbookId = ref(NONE);
const creating = reactive({ open: false, busy: false, kind: "category" as "category" | "cookbook", name: "" });
// making something new needs the right to organize, like Mealie's own organizer pages
const canOrganize = computed(() => !!useMealieAuth().user.value?.canOrganize);

const categoryItems = computed(() => [
  ...categories.value,
  ...(canOrganize.value ? [{ id: NEW, name: i18n.t("kh.drafts.where.new-category") }] : []),
]);
const books = computed(() => oneCategoryCookbooks(cookbooks.value));
const cookbookItems = computed(() => [
  { title: i18n.t("kh.drafts.where.none"), value: NONE },
  ...books.value.map(({ cookbook }) => ({ title: cookbook.name, value: cookbook.id })),
  ...(canOrganize.value ? [{ title: i18n.t("kh.drafts.where.new-cookbook"), value: NEW }] : []),
]);

const categoryIds = computed({
  get: () => chosen.value.map(category => category.id),
  set: (ids: string[]) => {
    if (ids.includes(NEW)) return ask("category");
    chosen.value = ids.flatMap(id => categories.value.filter(category => category.id === id).map(toRef));
  },
});

function toRef(category: CategoryOut): KhCategoryRef {
  return { id: category.id, name: category.name, slug: category.slug };
}

function ask(kind: "category" | "cookbook") {
  Object.assign(creating, { open: true, kind, name: "" });
}

/** Adds the category to the chosen ones, once. */
function add(category: CategoryOut) {
  if (!chosen.value.some(own => own.id === category.id)) chosen.value = [...chosen.value, toRef(category)];
}

/** A cookbook adds its category; "none" and the new-cookbook entry add nothing yet. */
function pickCookbook(id: string) {
  if (id === NEW) return ask("cookbook");
  cookbookId.value = id;
  const book = books.value.find(({ cookbook }) => cookbook.id === id);
  const category = categories.value.find(own => own.id === book?.categoryId);
  if (category) add(category);
}

/** Creates what the dialog asked for and keeps the dialog open when that fails. A category of that name that exists
 * is reused, so a new cookbook never doubles one and a second try after a failed cookbook does not either. */
async function create() {
  const name = creating.name.trim();
  if (!name || creating.busy) return;
  creating.busy = true;
  try {
    const category = findByName(categories.value, name) ?? (await categoryActions.createOne({ name } as CategoryOut));
    const book = category && creating.kind === "cookbook"
      ? await cookbookActions.createOne({ name, queryFilterString: cookbookFilter(category.id) } as CookBookCreate)
      : null;
    if (!category || (creating.kind === "cookbook" && !book)) {
      alert.error(i18n.t("kh.drafts.where.create-failed"));
      return;
    }
    add(category);
    if (book) cookbookId.value = book.id;
    creating.open = false;
  }
  finally {
    creating.busy = false;
  }
}
</script>
