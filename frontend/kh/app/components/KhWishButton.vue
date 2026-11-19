<!-- KH: "Wünsch ich mir" on the recipe page (D72): a toggle for the signed-in person's own wish, and a line saying who
     in the household wishes the recipe. -->
<template>
  <div class="d-print-none">
    <v-btn
      block
      size="large"
      class="mt-2"
      :variant="mine ? 'tonal' : 'outlined'"
      :color="mine ? 'primary' : undefined"
      :prepend-icon="$globals.icons.star"
      :loading="busy"
      :aria-pressed="mine"
      @click="toggle"
    >
      {{ $t("kh.wishes.button") }}
    </v-btn>
    <p v-if="line" class="text-body-2 text-medium-emphasis mt-1 mb-0" data-testid="wish-line">
      {{ line }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { KhWishesApi, type KhWish } from "../lib/api/wishes";
import { isWishedBy, joinNames, wishers } from "../lib/wishes";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

const props = defineProps<{ recipeId: string }>();

const api = new KhWishesApi(useRequests());
const i18n = useGlobalI18n();
const ownId = useMealieAuth().user.value?.id;
const wish = ref<KhWish>();
const busy = ref(false);
const mine = computed(() => isWishedBy(wish.value, ownId));

const line = computed(() => {
  if (!wish.value) return "";
  const names = wishers(wish.value, ownId, i18n.t("kh.wishes.you"));
  if (names.length === 1 && mine.value) return i18n.t("kh.wishes.line-self");
  return i18n.t(names.length === 1 ? "kh.wishes.line-one" : "kh.wishes.line-many", { names: joinNames(names, i18n.t("kh.wishes.and")) });
});

async function load() {
  const { data } = await api.list();
  wish.value = data?.find(item => item.recipe.id === props.recipeId);
}

async function toggle() {
  busy.value = true;
  const { error } = mine.value ? await api.unwish(props.recipeId) : await api.wish(props.recipeId);
  if (error) alert.error(i18n.t("events.something-went-wrong"));
  await load();
  busy.value = false;
}

// a failed request leaves the button without the line: the toggle itself still works
onMounted(load);
</script>
