<!-- KH: the start page's season row (D80): chips of what is in season now (tap = the start page's search for it) and below them recipes
of the group that use such a food. Only with the add-on "season" on; a failed request leaves the recipes out. -->
<template>
  <div v-if="khAddons.enabled.season" data-testid="season">
    <section class="mb-4">
      <h2 class="text-h6 mb-2">
        {{ $t("kh.season.title") }}
      </h2>
      <div class="d-flex flex-wrap ga-2">
        <v-chip v-for="item in items" :key="item.names[0]" color="primary" variant="tonal" @click="searchFor(seasonName(item, locale))">
          {{ seasonName(item, locale) }}
        </v-chip>
      </div>
    </section>
    <KhRecipeRow v-if="recipes.length" :title="$t('kh.season.recipes')" :recipes="recipes" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { khAddons } from "../composables/use-kh-addons";
import { KhSeasonApi, type KhSeasonRecipe } from "../lib/api/season";
import { inSeason, monthOf, seasonName, seasonTerms } from "../lib/season";
import { useRequests } from "~/composables/api/api-client";
import { useRecipeExplorerSearch } from "~/composables/use-recipe-explorer-search";

const { locale } = useI18n();
const MAX_CHIPS = 12;
const month = monthOf(new Date());
const items = inSeason(month).slice(0, MAX_CHIPS);
const recipes = ref<KhSeasonRecipe[]>([]);
const api = new KhSeasonApi(useRequests());
const route = useRoute();
const explorer = useRecipeExplorerSearch(computed(() => route.params.groupSlug as string));

/** Puts NAME into the start page's search; its auto-search runs it (when auto-search is off, it is run here). */
function searchFor(name: string) {
  explorer.state.value.search = name;
  if (!explorer.state.value.auto) void explorer.search();
}

// the add-on switches arrive after the page: ask the server only once the add-on is known to be on
watch(() => khAddons.enabled.season, async (on) => {
  if (!on) return;
  recipes.value = (await api.get(seasonTerms(month))).data?.recipes ?? [];
}, { immediate: true });
</script>
