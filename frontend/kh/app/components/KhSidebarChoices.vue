<!-- KH: the tick list of what the side menu shows (D58), used by the settings page and by "Anpassen" in the side menu itself. -->
<template>
  <v-list rounded="lg" class="py-2 px-4">
    <p class="text-body-2 text-medium-emphasis mb-2">
      {{ $t("kh.nav.sidebar-hint") }}
    </p>
    <v-list-item v-for="target in entries" :key="target.key" :title="$t(target.title)" class="px-0">
      <template #append>
        <v-checkbox
          :model-value="!khSidebar.hidden.includes(target.key)"
          color="primary"
          density="compact"
          hide-details
          :label="$t('kh.nav.in-sidebar')"
          @update:model-value="setInSidebar(target.key, !!$event)"
        />
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
import { sidebarChoices } from "~~/kh/app/composables/use-kh-navigation";
import { khSidebar, saveKhSidebar } from "~~/kh/app/composables/use-kh-sidebar";

const route = useRoute();
const auth = useMealieAuth();
const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");
const entries = computed(() => sidebarChoices(groupSlug.value));

/** Shows or hides one entry of the side menu and saves the choice right away. */
function setInSidebar(key: string, shown: boolean) {
  void saveKhSidebar(shown ? khSidebar.hidden.filter(hidden => hidden !== key) : [...khSidebar.hidden, key]);
}
</script>
