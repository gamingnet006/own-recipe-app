<!-- KH: the bar at the bottom on phones and upright iPads (D38): recipes, the intake with its number of drafts,
the shopping list and More, from the shared list of destinations. -->
<template>
  <v-bottom-navigation
    :model-value="active"
    grow
    color="primary"
    class="d-print-none"
    :aria-label="$t('kh.nav.main')"
  >
    <v-btn
      v-for="target in targets"
      :key="target.key"
      :value="target.key"
      :active="target.key === active"
      :to="target.to"
      :aria-current="target.key === active ? 'page' : undefined"
      :aria-label="target.key === 'intake' && count ? $t('kh.nav.intake-waiting', { count }, count) : undefined"
    >
      <v-badge v-if="target.key === 'intake' && count" :content="count" color="primary">
        <v-icon :icon="icon(target.icon)" />
      </v-badge>
      <v-icon v-else :icon="icon(target.icon)" />
      <span>{{ $t(target.title) }}</span>
    </v-btn>
  </v-bottom-navigation>
</template>

<script setup lang="ts">
import { activeTab, barTargets, useKhShoppingTarget } from "../composables/use-kh-navigation";
import { useKhDraftCount } from "../composables/use-kh-drafts";

const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();
const { count } = useKhDraftCount();
const shoppingTo = useKhShoppingTarget();

const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const targets = computed(() => barTargets(groupSlug.value, shoppingTo.value));
const active = computed(() => activeTab(route.path, groupSlug.value));

/** One of Mealie's icons by its name in the list of destinations. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}
</script>
