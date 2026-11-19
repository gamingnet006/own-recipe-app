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
        {{ $t("kh.nav.sidebar") }}
      </h2>
      <v-list rounded="lg" class="py-2 px-4">
        <p class="text-body-2 text-medium-emphasis mb-2">
          {{ $t("kh.nav.sidebar-hint") }}
        </p>
        <v-list-item v-for="target in sidebarEntries" :key="target.key" :title="$t(target.title)" class="px-0">
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
    </section>

    <section v-if="khOn.oven" class="mb-4">
      <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
        {{ $t("kh.oven.title") }}
      </h2>
      <v-list rounded="lg" class="py-2 px-4">
        <v-radio-group v-model="oven" color="primary" :hint="$t('kh.oven.hint')" persistent-hint>
          <v-radio value="conventional" :label="$t('kh.oven.conventional')" />
          <v-radio value="fan" :label="$t('kh.oven.fan')" />
        </v-radio-group>
      </v-list>
    </section>

    <section v-if="khOn.nutrition" class="mb-4">
      <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
        {{ $t("kh.nutrition.title") }}
      </h2>
      <v-list rounded="lg" class="py-2 px-4">
        <v-switch
          v-model="showNutrition"
          color="primary"
          :label="$t('kh.nutrition.show')"
          :hint="$t('kh.nutrition.show-hint')"
          persistent-hint
        />
      </v-list>
    </section>

    <section v-if="khOn.clock" class="mb-4">
      <h2 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
        {{ $t("kh.timer.title") }}
      </h2>
      <v-list v-if="!clockOffered" rounded="lg" class="py-2 px-4">
        <p class="text-body-2">
          {{ $t("kh.timer.clock-ios-only") }}
        </p>
      </v-list>
      <v-list v-else rounded="lg" class="py-2 px-4">
        <v-switch
          v-model="clockEnabled"
          color="primary"
          :label="$t('kh.timer.clock-switch')"
          :hint="$t('kh.timer.clock-hint')"
          persistent-hint
        />
        <!-- Optional ready-made shortcut (KH_CLOCK_SHORTCUT_URL); the steps below stay as the fallback -->
        <v-btn
          v-if="$khFeatures.clockShortcutUrl"
          :href="$khFeatures.clockShortcutUrl"
          target="_blank"
          rel="noopener"
          color="primary"
          class="mt-2"
          block
        >
          {{ $t("kh.timer.clock-add") }}
        </v-btn>
        <v-expansion-panels variant="accordion" class="mt-2">
          <v-expansion-panel :title="$t('kh.timer.clock-setup')">
            <v-expansion-panel-text>
              <ol class="pl-4">
                <li v-for="n in 4" :key="n" class="mb-1">
                  {{ $t(`kh.timer.clock-step-${n}`) }}
                </li>
              </ol>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <v-text-field
          v-if="clockEnabled"
          v-model="clockName"
          :label="$t('kh.timer.clock-name')"
          class="mt-4"
          @blur="clockName = clockName.trim() || DEFAULT_CLOCK_SHORTCUT"
        />
        <v-btn variant="tonal" class="mt-2" block @click="tryClockShortcut">
          {{ $t("kh.timer.clock-try") }}
        </v-btn>
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
          :to="target.key === 'switch' ? undefined : target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
          @click="target.key === 'switch' && (switchDialog = true)"
        />
        <v-list-item
          v-if="user?.canInvite"
          :prepend-icon="$globals.icons.accountPlusOutline"
          :title="$t('kh.nav.invite')"
          @click="inviteDialog = true"
        />
        <v-list-item :prepend-icon="$globals.icons.wave" :title="$t('kh.tour.view')" @click="tourOpen = true" />
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
      <a :href="$khFeatures.sourceUrl" target="_blank" rel="noopener">{{ $t("kh.nav.source") }}</a>
    </p>

    <UserInviteDialog v-model="inviteDialog" />
    <LanguageDialog v-model="languageDialog" />
    <KhAccountSwitch v-model="switchDialog" />
    <KhTour v-model="tourOpen" />
  </v-container>
</template>

<script setup lang="ts">
import {
  moreSections,
  settingsTargets,
  sidebarChoices,
  useKhShoppingTarget,
} from "~~/kh/app/composables/use-kh-navigation";
import { khSidebar, saveKhSidebar } from "~~/kh/app/composables/use-kh-sidebar";
import { clockTimerUrl, DEFAULT_CLOCK_SHORTCUT, useKhClockSetting } from "~~/kh/app/composables/use-kh-timers";
import { useKhNutritionSetting } from "~~/kh/app/lib/nutrition";
import { useKhOn } from "~~/kh/app/composables/use-kh-addons";
import { useKhAccounts } from "~~/kh/app/composables/use-kh-accounts";
import { useKhOven } from "~~/kh/app/lib/oven";
import { alert } from "~/composables/use-toast";
import { useToggleDarkMode } from "~/composables/use-utils";

definePageMeta({
  middleware: ["auth", "group-only"],
});

// Where the source of Mealie can be read (AGPL); this fork's comes from KH_SOURCE_URL
const MEALIE_URL = "https://github.com/mealie-recipes/mealie";

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const auth = useMealieAuth();
const toggleDark = useToggleDarkMode();
const oven = useKhOven();
const khOn = useKhOn();
const showNutrition = useKhNutritionSetting();
const { enabled: clockEnabled, name: clockName, offered: clockOffered } = useKhClockSetting();

/** Starts a one-minute Clock timer through the shortcut, so locking the phone proves that it rings. */
function tryClockShortcut() {
  location.href = clockTimerUrl(clockName.value, 60);
}

useSeoMeta({ title: i18n.t("kh.nav.more") });

const user = computed(() => auth.user.value);
const inviteDialog = ref(false);
const languageDialog = ref(false);
const switchDialog = ref(false);
const tourOpen = ref(false); // shown again any time, without a call to the server (D59)
const { accounts, load: loadAccounts } = useKhAccounts();
onMounted(loadAccounts);

const shoppingTo = useKhShoppingTarget();
const sidebarEntries = computed(() => sidebarChoices(route.params.groupSlug as string));

/** Shows or hides one entry of the side menu and saves the choice right away. */
function setInSidebar(key: string, shown: boolean) {
  void saveKhSidebar(shown ? khSidebar.hidden.filter(hidden => hidden !== key) : [...khSidebar.hidden, key]);
}

const sections = computed(() => {
  const { plan, collection } = moreSections(
    route.params.groupSlug as string,
    user.value?.id ?? "",
    undefined,
    undefined,
    shoppingTo.value,
  );
  return [
    { title: "kh.nav.plan", targets: plan },
    { title: "kh.nav.collection", targets: collection },
  ];
});
const settings = computed(() =>
  settingsTargets(
    { canOrganize: user.value?.canOrganize, admin: user.value?.admin, linked: accounts.value.length > 0 },
    route.params.groupSlug as string,
  ),
);

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
