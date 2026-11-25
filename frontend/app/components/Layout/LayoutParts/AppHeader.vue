<template>
  <!-- KH: a light header as in the mockup; the accent color stays for the logo and the buttons (D38) -->
  <v-app-bar
    clipped-left
    density="compact"
    app
    color="surface"
    flat
    border="b"
    class="d-print-none"
  >
    <slot />
    <RouterLink :to="routerLink">
      <v-btn
        icon
        color="primary"
      >
        <!-- KH: Kochheft's logo replaces Mealie's icon when no custom logo is set (D49) -->
        <KhLogo :size="40" /> <!-- KH: drawn in the accent colour (wave 2) -->
      </v-btn>
    </RouterLink>

    <div
      btn
      class="pl-2"
    >
      <v-toolbar-title
        style="cursor: pointer"
        @click="$router.push(routerLink)"
      >
        {{ appName }} <!-- KH: Kochheft or Cookbook by language (wave 2) -->
      </v-toolbar-title>
    </div>
    <RecipeDialogSearch ref="domSearchDialog" />

    <v-spacer />

    <!-- Navigation Menu -->
    <template v-if="menu">
      <!-- KH: the bell with notices about the AI providers, for whoever manages them (D39) -->
      <KhBell v-if="loggedIn && auth.user.value?.canManage" />
      <v-responsive
        v-if="!xs"
        max-width="250"
        @click="activateSearch"
      >
        <v-text-field
          readonly
          class="mt-1"
          rounded
          variant="solo-filled"
          density="compact"
          flat
          :prepend-inner-icon="$globals.icons.search"
          :placeholder="$t('search.search-hint')"
        />
      </v-responsive>
      <v-btn
        v-else
        icon
        @click="activateSearch"
      >
        <v-icon> {{ $globals.icons.search }}</v-icon>
      </v-btn>
      <!-- KH: on phones signing out sits under More (D38) -->
      <v-btn
        v-if="loggedIn"
        v-show="mdAndUp && !khCookScreen"
        :variant="smAndUp ? 'text' : undefined"
        :icon="xs"
        @click="logout()"
      >
        <v-icon :start="smAndUp">
          {{ $globals.icons.logout }}
        </v-icon>
        {{ smAndUp ? $t("user.logout") : "" }}
      </v-btn>
      <v-btn
        v-else
        variant="text"
        nuxt
        to="/login"
      >
        <v-icon start>
          {{ $globals.icons.user }}
        </v-icon>
        {{ $t("user.login") }}
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script setup lang="ts">
import { useKhAppName } from "~~/kh/app/composables/use-kh-app-name"; // KH: wave 2
import { useKhCookScreen } from "~~/kh/app/composables/use-kh-cook-screen"; // KH: D76
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type RecipeDialogSearch from "~/components/Domain/Recipe/RecipeDialogSearch.vue";

defineProps({
  menu: {
    type: Boolean,
    default: true,
  },
});
const appName = useKhAppName(); // KH: wave 2
const auth = useMealieAuth();
const { loggedIn } = useLoggedInState();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");
const { xs, smAndUp, mdAndUp } = useDisplay(); // KH: mdAndUp for signing out (D38)
const khCookScreen = useKhCookScreen(); // KH: no sign-out in cook mode (D76)

const routerLink = computed(() => groupSlug.value ? `/g/${groupSlug.value}` : "/");
const domSearchDialog = ref<InstanceType<typeof RecipeDialogSearch> | null>(null);

function activateSearch() {
  domSearchDialog.value?.open();
}

function handleKeyEvent(e: KeyboardEvent) {
  const activeTag = document.activeElement?.tagName;
  if (e.key === "/" && activeTag !== "INPUT" && activeTag !== "TEXTAREA") {
    e.preventDefault();
    activateSearch();
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeyEvent);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleKeyEvent);
});

async function logout() {
  try {
    await auth.signOut("/login?direct=1");
  }
  catch (e) {
    console.error(e);
  }
}
</script>

<style scoped>
.v-toolbar {
  z-index: 2010 !important;
}
</style>
