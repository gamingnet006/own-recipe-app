<!-- KH: the arrow at the top of every sub-page: the installed app (Dock, home screen) has no browser back. It goes back in
the history, or to the page of its tab when the page was opened directly (see backTarget). -->
<template>
  <v-btn v-if="fallback" icon :aria-label="$t('general.back')" @click="goBack">
    <v-icon :icon="$globals.icons.arrowLeftBold" />
  </v-btn>
</template>

<script setup lang="ts">
import { backTarget } from "../composables/use-kh-navigation";
import { useKhCookScreen } from "../composables/use-kh-cook-screen";

const { $globals } = useNuxtApp();
const route = useRoute();
const router = useRouter();
const auth = useMealieAuth();
const cook = useKhCookScreen();

const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");
const fallback = computed(() => (auth.user.value ? backTarget(route.path, groupSlug.value, cook.value) : null));

/** Back where the person came from, or to the fallback page when there is no history. */
function goBack() {
  if (window.history.state?.back) router.back();
  else if (fallback.value) void router.push(fallback.value);
}
</script>
