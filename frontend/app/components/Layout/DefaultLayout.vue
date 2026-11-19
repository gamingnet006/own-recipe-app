<template>
  <v-app dark>
    <TheSnackbar />

    <AppHeader>
      <!-- KH: below 840 px the bar at the bottom replaces menu button and side menu (D38) -->
      <v-btn
        v-if="khWide && !khCookScreen"
        icon
        @click.stop="sidebar = !sidebar"
      >
        <v-icon> {{ $globals.icons.menu }}</v-icon>
      </v-btn>
    </AppHeader>

    <KhBottomNav v-if="!khWide && !khCookScreen" />
    <!-- KH: the running timers and their alarm on every page (D42) -->
    <KhTimers compact />
    <AppSidebar
      v-if="khWide && !khCookScreen"
      v-model="sidebar"
      mobile-breakpoint="md"
      :top-link="topLinks"
      :secondary-links="cookbookLinks || []"
    >
      <v-menu
        offset-y
        nudge-bottom="5"
        close-delay="50"
        nudge-right="15"
      >
        <template #activator="{ props }">
          <v-btn
            v-if="isOwnGroup"
            rounded
            size="large"
            class="ml-2 mt-3"
            v-bind="props"
            variant="elevated"
            elevation="2"
            :color="$vuetify.theme.current.dark ? 'background-lighten-1' : 'background-darken-1'"
          >
            <v-icon
              start
              size="large"
              color="primary"
            >
              {{ $globals.icons.createAlt }}
            </v-icon>
            {{ $t("general.create") }}
          </v-btn>
        </template>
        <v-list
          density="comfortable"
          class="mb-0 mt-1 py-0"
          variant="flat"
        >
          <template v-for="(item, index) in createLinks">
            <div
              v-if="!item.hide"
              :key="item.title"
            >
              <v-divider
                v-if="item.insertDivider"
                :key="index"
                class="mx-2"
              />
              <v-list-item
                v-if="!item.restricted || isOwnGroup"
                :key="item.title"
                :to="item.to"
                exact
                class="my-1"
              >
                <template #prepend>
                  <v-icon
                    size="40"
                    :icon="item.icon"
                  />
                </template>
                <v-list-item-title class="font-weight-medium" style="font-size: small;">
                  {{ item.title }}
                </v-list-item-title>
                <v-list-item-subtitle class="font-weight-medium" style="font-size: small;">
                  {{ item.subtitle }}
                </v-list-item-subtitle>
              </v-list-item>
            </div>
          </template>
        </v-list>
      </v-menu>
    </AppSidebar>
    <v-main class="pt-12">
      <v-scroll-x-transition>
        <div>
          <NuxtPage />
        </div>
      </v-scroll-x-transition>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { SideBarLink } from "~/types/application-types";
import { useCookbookPreferences } from "~/composables/use-users/preferences";
import { useCookbookStore, usePublicCookbookStore } from "~/composables/store/use-cookbook-store";
import type { CookBookOut } from "~/lib/api/types/cookbook";
import { useKhDraftCount } from "~~/kh/app/composables/use-kh-drafts"; // KH: drafts counter for the menu
import { useKhCookScreen } from "~~/kh/app/composables/use-kh-cook-screen"; // KH: D76
import { useKhAddonsLoader } from "~~/kh/app/composables/use-kh-addons"; // KH: add-on switches (D46)
// KH: shared destinations (D38)
import {
  type KhNavTarget,
  sidebarTargets,
  useKhSidebar,
} from "~~/kh/app/composables/use-kh-navigation";

const i18n = useI18n();
const { $globals } = useNuxtApp();
const display = useDisplay();
const auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();

const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug as string || auth.user.value?.groupSlug || "");

// KH: the drafts number for the menu, loaded again on every page change (phase 2)
const { count: khDraftCount, refresh: refreshKhDraftCount } = useKhDraftCount();
watch(() => route.path, () => {
  if (isOwnGroup.value) refreshKhDraftCount();
}, { immediate: true });

const cookbookPreferences = useCookbookPreferences();
const ownCookbookStore = computed(() => isOwnGroup.value ? useCookbookStore(i18n) : null);
const publicCookbookStoreCache = ref<Record<string, ReturnType<typeof usePublicCookbookStore>>>({});

function getPublicCookbookStore(slug: string) {
  if (!publicCookbookStoreCache.value[slug]) {
    publicCookbookStoreCache.value[slug] = usePublicCookbookStore(slug, i18n);
  }
  return publicCookbookStoreCache.value[slug];
}

const cookbooks = computed(() => {
  if (ownCookbookStore.value) {
    return ownCookbookStore.value.store.value;
  }
  else if (groupSlug.value) {
    const publicStore = getPublicCookbookStore(groupSlug.value);
    return unref(publicStore.store);
  }
  return [];
});

// KH: from 840 px (iPad landscape, computer) Mealie's side menu stands open beside the page, below it the bar at the
// bottom (D38); mobile-breakpoint="md" above keeps the menu from covering the page up to Vuetify's 1145 px
const khWide = computed(() => display.mdAndUp.value);
const sidebar = useKhSidebar(khWide);
const khCookScreen = useKhCookScreen(); // KH: cook mode hides bar, side menu and sign-out (D76)
useKhAddonsLoader(); // KH: D46

function cookbookAsLink(cookbook: CookBookOut): SideBarLink {
  return {
    key: cookbook.slug || "",
    icon: $globals.icons.pages,
    title: cookbook.name,
    to: `/g/${groupSlug.value}/cookbooks/${cookbook.slug || ""}`,
    restricted: false,
  };
}

const currentUserHouseholdId = computed(() => auth.user.value?.householdId);
const cookbookLinks = computed<SideBarLink[]>(() => {
  if (!cookbooks.value?.length) {
    return [];
  }

  const sortedCookbooks = [...cookbooks.value].sort((a, b) => (a.position || 0) - (b.position || 0));

  const ownLinks: SideBarLink[] = [];
  const links: SideBarLink[] = [];
  const cookbooksByHousehold = sortedCookbooks.reduce((acc, cookbook) => {
    const householdName = cookbook.household?.name || "";
    (acc[householdName] ||= []).push(cookbook);
    return acc;
  }, {} as Record<string, CookBookOut[]>);

  Object.entries(cookbooksByHousehold).forEach(([householdName, cookbooks]) => {
    if (!cookbooks.length) {
      return;
    }
    if (cookbooks[0].householdId === currentUserHouseholdId.value) {
      ownLinks.push(...cookbooks.map(cookbookAsLink));
    }
    else {
      links.push({
        key: householdName,
        icon: $globals.icons.book,
        title: householdName,
        children: cookbooks.map(cookbookAsLink),
        restricted: false,
      });
    }
  });

  links.sort((a, b) => a.title.localeCompare(b.title));
  if (auth.user.value && cookbookPreferences.value.hideOtherHouseholds) {
    return ownLinks;
  }
  else {
    return [...ownLinks, ...links];
  }
});

const createLinks = computed(() => [
  // KH: Mealie's "Import" and "Import with AI" become one entry for the drafts intake, where every recipe
  // gets a review before it is saved (phase 2)
  {
    insertDivider: false,
    icon: $globals.icons.import,
    title: i18n.t("kh.drafts.add-recipe"),
    subtitle: i18n.t("kh.drafts.add-recipe-subtitle"),
    to: `/g/${groupSlug.value}/drafts`, // KH: the intake and the drafts are one page (D38)
    restricted: true,
    hide: false,
  },
  {
    insertDivider: true,
    icon: $globals.icons.edit,
    title: i18n.t("general.create"),
    subtitle: i18n.t("new-recipe.create-manually"),
    to: `/g/${groupSlug.value}/r/create/new`,
    restricted: true,
    hide: false,
  },
]);

// KH: the side menu shows the shared destinations (D38), the intake with its number of drafts; as in Mealie, only
// the recipes and the finder show for visitors of a public group
const KH_PUBLIC_TARGETS = ["recipes", "finder"];
const topLinks = computed<SideBarLink[]>(() => sidebarTargets(groupSlug.value).map(khSideBarLink));

/** KH: one destination of the shared list as an entry of Mealie's side menu. */
function khSideBarLink(target: KhNavTarget): SideBarLink {
  return {
    key: target.key,
    icon: ($globals.icons as Record<string, string>)[target.icon] ?? "",
    to: target.children ? undefined : target.to,
    title: target.key === "intake"
      ? i18n.t("kh.nav.intake-count", { count: khDraftCount.value })
      : i18n.t(target.title),
    restricted: !KH_PUBLIC_TARGETS.includes(target.key),
    children: target.children?.map(khSideBarLink),
  };
}
</script>
