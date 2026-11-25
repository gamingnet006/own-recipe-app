<!-- KH: the one settings page (wave 2), reached from More, Mealie's settings links and the side menu: "Ich" (account and
look), "Auf diesem Gerät" (setup, oven, nutrition, timer), "Familie & Verwaltung" (admins) and "Erweitert". -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.settings") }}
      </template>
    </BasePageTitle>

    <section class="mb-6">
      <h2 class="text-h6 mb-1">
        {{ $t("kh.settings.me") }}
      </h2>
      <v-list rounded="lg" class="py-0">
        <template v-for="target in sections.me" :key="target.key">
          <v-list-item
            :to="isDialog(target) ? undefined : target.to"
            :prepend-icon="icon(target.icon)"
            :title="$t(target.title)"
            @click="openDialog(target)"
          />
          <template v-if="target.key === 'profileEdit'">
            <v-list-item :prepend-icon="$globals.icons.translate" :title="$t('sidebar.language')" @click="languageDialog = true" />
            <!-- KH: the theme buttons sit under the label on narrow screens, so the label stays readable -->
            <v-list-item class="kh-theme-row" :prepend-icon="$vuetify.theme.current.dark ? $globals.icons.weatherNight : $globals.icons.weatherSunny" :title="$t('kh.theme.title')">
              <template #append>
                <KhThemeChoice />
              </template>
            </v-list-item>
            <KhAccentRow />
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
          </template>
        </template>
      </v-list>
      <div v-if="khWide" class="mt-4">
        <h3 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.nav.sidebar") }}
        </h3>
        <KhSidebarChoices />
      </div>
    </section>

    <section class="mb-6">
      <h2 class="text-h6 mb-1">
        {{ $t("kh.settings.device") }}
      </h2>
      <v-list rounded="lg" class="py-0 mb-4">
        <v-list-item
          v-for="target in sections.device"
          :key="target.key"
          :to="target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
        />
      </v-list>
      <section v-if="khOn.oven" class="mb-4">
        <h3 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.oven.title") }}
        </h3>
        <v-list rounded="lg" class="py-2 px-4">
          <v-radio-group v-model="oven" color="primary" :hint="$t('kh.oven.hint')" persistent-hint>
            <v-radio value="conventional" :label="$t('kh.oven.conventional')" />
            <v-radio value="fan" :label="$t('kh.oven.fan')" />
          </v-radio-group>
        </v-list>
      </section>

      <section v-if="khOn.nutrition" class="mb-4">
        <h3 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.nutrition.title") }}
        </h3>
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
        <h3 class="text-subtitle-1 font-weight-bold text-medium-emphasis mb-1">
          {{ $t("kh.timer.title") }}
        </h3>
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
            v-if="clockShortcutUrl"
            :href="clockShortcutUrl"
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
            @blur="clockName = clockName.trim()"
          />
          <v-btn variant="tonal" class="mt-2" block @click="tryClockShortcut">
            {{ $t("kh.timer.clock-try") }}
          </v-btn>
        </v-list>
      </section>
    </section>

    <section v-if="sections.family.length" class="mb-6">
      <h2 class="text-h6 mb-1">
        {{ $t("kh.settings.family") }}
      </h2>
      <v-list rounded="lg" class="py-0">
        <v-list-item
          v-for="target in sections.family"
          :key="target.key"
          :to="isDialog(target) ? undefined : target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
          @click="openDialog(target)"
        />
      </v-list>
    </section>

    <section v-if="sections.advanced.length" class="mb-6">
      <h2 class="text-h6 mb-1">
        {{ $t("kh.settings.advanced") }}
      </h2>
      <v-list rounded="lg" class="py-0">
        <v-list-item
          v-for="target in sections.advanced"
          :key="target.key"
          :to="target.to"
          :prepend-icon="icon(target.icon)"
          :title="$t(target.title)"
        />
      </v-list>
    </section>

    <UserInviteDialog v-model="inviteDialog" />
    <KhAccountSwitch v-model="switchDialog" />
    <LanguageDialog v-model="languageDialog" />
  </v-container>
</template>

<script setup lang="ts">
import { settingsSections, type KhNavTarget } from "~~/kh/app/composables/use-kh-navigation";
import { clockTimerUrl, useKhClockSetting } from "~~/kh/app/composables/use-kh-timers";
import { shortcutUrlsFor } from "~~/kh/app/lib/device-setup";
import { useKhNutritionSetting } from "~~/kh/app/lib/nutrition";
import { useKhOn } from "~~/kh/app/composables/use-kh-addons";
import { useKhAccounts } from "~~/kh/app/composables/use-kh-accounts";
import { khSidebar, saveKhSimple } from "~~/kh/app/composables/use-kh-sidebar";
import { useKhOven } from "~~/kh/app/lib/oven";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const { $globals, $khFeatures } = useNuxtApp();
const clockShortcutUrl = computed(() => shortcutUrlsFor($khFeatures.shortcutUrls, i18n.locale.value).clock); // KH: per language
const route = useRoute();
const auth = useMealieAuth();
const oven = useKhOven();
const khOn = useKhOn();
const showNutrition = useKhNutritionSetting();
const { enabled: clockEnabled, name: clockName, offered: clockOffered } = useKhClockSetting(() => i18n.locale.value); // KH: the default shortcut name follows the language
const khWide = useDisplay().mdAndUp; // the side menu only exists from 840 px, so only there is it set up

/** Starts a one-minute Clock timer through the shortcut, so locking the phone proves that it rings. */
function tryClockShortcut() {
  location.href = clockTimerUrl(clockName.value, 60);
}

useSeoMeta({ title: i18n.t("kh.nav.settings") });

const user = computed(() => auth.user.value);
const inviteDialog = ref(false);
const switchDialog = ref(false);
const languageDialog = ref(false);
const { accounts, load: loadAccounts } = useKhAccounts();
onMounted(loadAccounts);

const sections = computed(() =>
  settingsSections(
    { ...user.value, linked: accounts.value.length > 0 },
    route.params.groupSlug as string,
  ),
);

/** The two rows that open a dialog instead of a page. */
const isDialog = (target: KhNavTarget) => target.key === "switch" || target.key === "invite";

function openDialog(target: KhNavTarget) {
  if (target.key === "switch") switchDialog.value = true;
  else if (target.key === "invite") inviteDialog.value = true;
}

/** One of Mealie's icons by its name in the list of destinations. */
function icon(name: string): string {
  return ($globals.icons as Record<string, string>)[name] ?? "";
}
</script>

<style scoped>
@media (max-width: 599px) {
  .kh-theme-row {
    grid-template-areas: "prepend content" ". append";
    grid-template-columns: max-content 1fr;
  }
  .kh-theme-row :deep(.v-list-item__append) {
    justify-self: start;
    padding-bottom: 8px;
  }
}
</style>
