<!-- KH: the More page of the bar at the bottom (D38, D76): planning, the collection, one row to the settings page, help
and the account, so a phone reaches everything the side menu holds on bigger screens. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.more") }}
      </template>
    </BasePageTitle>

    <!-- KH: the order and the fold of the sections follow the simple view (D79) -->
    <template v-for="key in shown" :key="key">
      <section v-if="key === 'plan' || key === 'collection'" class="mb-4">
        <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t(key === "plan" ? "kh.nav.plan" : "kh.nav.collection") }}
        </h2>
        <v-list rounded="lg" class="py-0">
          <v-list-item
            v-for="target in lists[key]"
            :key="target.key"
            :to="target.to"
            :prepend-icon="icon(target.icon)"
            :title="$t(target.title)"
          />
        </v-list>
      </section>

      <section v-else-if="key === 'settings'" class="mb-4">
        <v-list rounded="lg" class="py-0">
          <v-list-item
            v-for="target in lists.settings"
            :key="target.key"
            :to="target.to"
            :prepend-icon="icon(target.icon)"
            :title="$t(target.title)"
          />
        </v-list>
      </section>

      <section v-else-if="key === 'help'" class="mb-4">
        <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.nav.help") }}
        </h2>
        <v-list rounded="lg" class="py-0">
          <v-list-item :prepend-icon="$globals.icons.wave" :title="$t('kh.tour.view')" @click="tourOpen = true" />
          <!-- KH: setup page and all news (D68, D69) -->
          <v-list-item :prepend-icon="$globals.icons.cellphone" :title="$t('kh.setup.title')" :to="SETUP_PATH" />
          <v-list-item :prepend-icon="$globals.icons.star" :title="$t('kh.news.menu')" @click="newsOpen = true" />
          <v-list-item
            v-for="target in lists.help"
            :key="target.key"
            :to="target.to"
            :prepend-icon="icon(target.icon)"
            :title="$t(target.title)"
          />
        </v-list>
      </section>

      <section v-else class="mb-4">
        <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.nav.account") }}
        </h2>
        <v-list rounded="lg" class="py-0">
          <!-- KH: the simple view (D79) -->
          <v-list-item :title="$t('kh.simple.title')" :subtitle="$t('kh.simple.text')">
            <template #append>
              <v-switch
                :model-value="khSidebar.simple"
                :aria-label="$t('kh.simple.title')"
                color="primary"
                hide-details
                density="compact"
                @update:model-value="saveKhSimple(!!$event)"
              />
            </template>
          </v-list-item>
          <v-list-item
            :prepend-icon="$globals.icons.translate"
            :title="$t('sidebar.language')"
            @click="languageDialog = true"
          />
          <!-- KH: System / Light / Dark instead of Mealie's one toggle -->
          <v-list-item :prepend-icon="$vuetify.theme.current.dark ? $globals.icons.weatherNight : $globals.icons.weatherSunny" :title="$t('kh.theme.title')">
            <template #append>
              <KhThemeChoice />
            </template>
          </v-list-item>
          <v-list-item
            :prepend-icon="$globals.icons.logout"
            :title="$t('user.logout')"
            @click="logout"
          />
          <!-- KH: the recipes stay in the family (D78) -->
          <v-list-item
            :prepend-icon="$globals.icons.delete"
            :title="$t('kh.account-delete.entry')"
            base-color="error"
            @click="deleteOpen = true"
          />
        </v-list>
      </section>
    </template>

    <v-btn v-if="layout.folded.length && !showFolded" block variant="tonal" class="mb-4" @click="showFolded = true">
      {{ $t("kh.simple.show-more") }}
    </v-btn>

    <p class="text-center text-body-2 text-medium-emphasis">
      {{ appName }} ·
      <a :href="MEALIE_URL" target="_blank" rel="noopener">{{ $t("kh.nav.based-on-mealie") }}</a> ·
      <a :href="$khFeatures.sourceUrl" target="_blank" rel="noopener">{{ $t("kh.nav.source") }}</a>
    </p>

    <LanguageDialog v-model="languageDialog" />
    <KhDeleteAccountDialog v-model="deleteOpen" />
    <KhTour v-model="tourOpen" />
    <KhNews v-model="newsOpen" :news="allNews" />
  </v-container>
</template>

<script setup lang="ts">
import { useKhAppName } from "~~/kh/app/composables/use-kh-app-name";
import { moreLayout, moreSections } from "~~/kh/app/composables/use-kh-navigation";
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { khSidebar, saveKhSimple } from "~~/kh/app/composables/use-kh-sidebar";
import { SETUP_PATH } from "~~/kh/app/lib/device-setup";
import { forAddons, WHATS_NEW } from "~~/kh/app/lib/whats-new";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["auth", "group-only"],
});

// Where the source of Mealie can be read (AGPL); this fork's comes from KH_SOURCE_URL
const MEALIE_URL = "https://github.com/mealie-recipes/mealie";

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();

useSeoMeta({ title: i18n.t("kh.nav.more") });

const appName = useKhAppName();
const languageDialog = ref(false);
const deleteOpen = ref(false);
const tourOpen = ref(false); // shown again any time, without a call to the server (D59)
const newsOpen = ref(false); // all versions any time, without a call to the server (D69)
const allNews = computed(() => forAddons(WHATS_NEW, khAddons.enabled, !!auth.user.value?.admin));

const lists = computed(() => moreSections(route.params.groupSlug as string, auth.user.value?.id ?? ""));
const layout = computed(() => moreLayout(khSidebar.simple));
const showFolded = ref(false); // "Show more" in the simple view
const shown = computed(() => [...layout.value.first, ...(showFolded.value ? layout.value.folded : [])]);

/** One of Mealie's icons by its name in the list of destinations. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}

/** Signs out as the header does on bigger screens. */
async function logout() {
  try {
    await auth.signOut("/login?direct=1");
  }
  catch {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}
</script>
