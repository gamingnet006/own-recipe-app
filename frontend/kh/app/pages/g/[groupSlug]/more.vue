<!-- KH: the More page of the bar at the bottom (D38): planning, the collection and the settings, so a phone reaches
everything the side menu holds on bigger screens. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.more") }}
      </template>
    </BasePageTitle>

    <section v-for="section in sections" :key="section.title" class="mb-4">
      <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
        {{ $t(section.title) }}
      </h2>
      <v-list rounded="lg" class="py-0">
        <v-list-item
          v-for="target in section.targets"
          :key="target.key"
          :to="target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
        />
      </v-list>
    </section>

    <section class="mb-4">
      <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
        {{ $t("general.settings") }}
      </h2>
      <v-list rounded="lg" class="py-0">
        <v-list-item
          v-for="target in settings"
          :key="target.key"
          :to="target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
        />
        <v-list-item
          v-if="user?.canInvite"
          :prepend-icon="$globals.icons.accountPlusOutline"
          :title="$t('kh.nav.invite')"
          @click="inviteDialog = true"
        />
        <v-list-item
          :prepend-icon="$globals.icons.translate"
          :title="$t('sidebar.language')"
          @click="languageDialog = true"
        />
        <v-list-item
          :prepend-icon="$vuetify.theme.current.dark ? $globals.icons.weatherSunny : $globals.icons.weatherNight"
          :title="$vuetify.theme.current.dark ? $t('settings.theme.light-mode') : $t('settings.theme.dark-mode')"
          @click="toggleDark"
        />
        <v-list-item
          :prepend-icon="$globals.icons.logout"
          :title="$t('user.logout')"
          @click="logout"
        />
      </v-list>
    </section>

    <p class="text-center text-body-2 text-medium-emphasis">
      {{ $appInfo.brandingName }} ·
      <a :href="MEALIE_URL" target="_blank" rel="noopener">{{ $t("kh.nav.based-on-mealie") }}</a> ·
      <a :href="SOURCE_URL" target="_blank" rel="noopener">{{ $t("kh.nav.source") }}</a>
    </p>

    <UserInviteDialog v-model="inviteDialog" />
    <LanguageDialog v-model="languageDialog" />
  </v-container>
</template>

<script setup lang="ts">
import { moreSections, settingsTargets } from "~~/kh/app/composables/use-kh-navigation";
import { alert } from "~/composables/use-toast";
import { useToggleDarkMode } from "~/composables/use-utils";

definePageMeta({
  middleware: ["auth", "group-only"],
});

// Where the source of this fork and of Mealie can be read (AGPL)
const SOURCE_URL = "https://github.com/gamingnet006/own-recipe-app";
const MEALIE_URL = "https://github.com/mealie-recipes/mealie";

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();
const toggleDark = useToggleDarkMode();

useSeoMeta({ title: i18n.t("kh.nav.more") });

const user = computed(() => auth.user.value);
const inviteDialog = ref(false);
const languageDialog = ref(false);

const sections = computed(() => {
  const { plan, collection } = moreSections(route.params.groupSlug as string, user.value?.id ?? "");
  return [
    { title: "kh.nav.plan", targets: plan },
    { title: "kh.nav.collection", targets: collection },
  ];
});
const settings = computed(() => settingsTargets({ canOrganize: user.value?.canOrganize, admin: user.value?.admin }));

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
