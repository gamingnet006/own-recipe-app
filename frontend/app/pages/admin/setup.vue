<template>
  <v-container
    fluid
    class="d-flex justify-center  align-start  fill-height"
    :class="{
      'bg-off-white': !$vuetify.theme.current.dark && !isDark,
    }"
  >
    <!-- Header Toolbar -->
    <v-card class="elevation-4" width="1200" :class="{ 'my-10': $vuetify.display.mdAndUp }">
      <v-toolbar
        color="primary"
        class="d-flex justify-center"
        dark
      >
        <v-toolbar-title class="headline text-h4 text-center mx-0">
          Kochheft <!-- KH: own name (D83) -->
        </v-toolbar-title>
      </v-toolbar>

      <!-- Stepper Wizard -->
      <!-- KH: nine steps need the short header up to 1280 px (D83) -->
      <v-stepper v-model="currentPage" mobile-breakpoint="lg" alt-labels>
        <v-stepper-header>
          <v-stepper-item
            :value="Pages.LANDING"
            :icon="$globals.icons.wave"
            :complete="currentPage > Pages.LANDING"
            :color="getStepperColor(currentPage, Pages.LANDING)"
            :title="$t('general.start')"
          />
          <v-divider v-if="!rerun" /> <!-- KH: no account step when the wizard is opened again (D83) -->
          <v-stepper-item
            v-if="!rerun"
            :value="Pages.USER_INFO"
            :icon="$globals.icons.user"
            :complete="currentPage > Pages.USER_INFO"
            :color="getStepperColor(currentPage, Pages.USER_INFO)"
            :title="$t('user-registration.account-details')"
          />
          <v-divider />
          <v-stepper-item
            :value="Pages.PAGE_2"
            :icon="$globals.icons.cog"
            :complete="currentPage > Pages.PAGE_2"
            :color="getStepperColor(currentPage, Pages.PAGE_2)"
            :title="$t('settings.site-settings')"
          />
          <v-divider />
          <v-stepper-item
            :value="Pages.AI_PROVIDERS"
            :icon="$globals.icons.robot"
            :complete="currentPage > Pages.AI_PROVIDERS"
            :color="getStepperColor(currentPage, Pages.AI_PROVIDERS)"
            :title="$t('group.ai-provider-settings.ai-providers')"
          />
          <v-divider />
          <!-- KH: Kochheft's own steps (D83) -->
          <template v-for="step in KH_STEPS" :key="step.page">
            <v-stepper-item
              :value="step.page"
              :icon="$globals.icons[step.icon]"
              :complete="currentPage > step.page"
              :color="getStepperColor(currentPage, step.page)"
              :title="$t(step.title)"
            />
            <v-divider />
          </template>
          <v-stepper-item
            :value="Pages.CONFIRM"
            :icon="$globals.icons.chefHat"
            :complete="currentPage > Pages.CONFIRM"
            :color="getStepperColor(currentPage, Pages.CONFIRM)"
            :title="$t('admin.maintenance.summary-title')"
          />
          <v-divider />
          <v-stepper-item
            :value="Pages.END"
            :icon="$globals.icons.check"
            :complete="currentPage > Pages.END"
            :color="getStepperColor(currentPage, Pages.END)"
            :title="$t('admin.setup.setup-complete')"
          />
        </v-stepper-header>
        <v-progress-linear
          v-if="isSubmitting && currentPage === Pages.CONFIRM"
          color="primary"
          indeterminate
          class="mb-2"
        />

        <v-stepper-window :transition="false" class="stepper-window">
          <!-- LANDING -->
          <v-stepper-window-item :value="Pages.LANDING">
            <v-container class="mb-12">
              <AppLogo />
              <v-card-title class="text-headline-medium my-5 justify-center text-center text-break text-pre-wrap">
                {{ $t('kh.wizard.welcome') }} <!-- KH: own name (D83) -->
              </v-card-title>
              <p class="text-body-1 text-center">
                {{ $t('kh.wizard.previous') }} <!-- KH: own name (D83) -->
              </p>
              <v-btn
                to="backups"
                rounded
                variant="outlined"
                color="primary"
                class="text-subtitle-2 d-flex mx-auto my-3"
                style="width: fit-content;"
              >
                {{ $t('settings.backup.restore-backup') }}
              </v-btn>
              <v-btn
                :to="groupSlug ? `/g/${groupSlug}` : '/login'"
                rounded
                variant="outlined"
                color="grey-lighten-1"
                class="text-subtitle-2 d-flex mx-auto"
                style="width: fit-content;"
              >
                {{ $t('admin.setup.already-set-up-bring-to-homepage') }}
              </v-btn>
            </v-container>

            <v-card-actions class="justify-center flex-column py-8">
              <BaseButton
                size="large"
                color="primary"
                class="px-10"
                rounded
                :icon="$globals.icons.translate"
                @click="langDialog = true"
              >
                {{ $t('language-dialog.choose-language') }}
              </BaseButton>
            </v-card-actions>

            <v-stepper-actions
              class="justify-end"
              :disabled="isSubmitting"
              next-text="general.next"
              @click:next="onNext"
            >
              <template #next>
                <v-btn
                  variant="flat"
                  color="success"
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :text="$t('general.next')"
                  @click="onNext"
                />
              </template>
              <template #prev />
            </v-stepper-actions>
          </v-stepper-window-item>

          <!-- USER INFO -->
          <v-stepper-window-item :value="Pages.USER_INFO" eager>
            <v-container max-width="880">
              <UserRegistrationForm />
            </v-container>
            <v-stepper-actions
              :disabled="isSubmitting"
              prev-text="general.back"
              @click:prev="onPrev"
            >
              <template #next>
                <v-btn
                  variant="flat"
                  color="success"
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :text="$t('general.next')"
                  @click="onNext"
                />
              </template>
            </v-stepper-actions>
          </v-stepper-window-item>

          <!-- COMMON SETTINGS -->
          <v-stepper-window-item :value="Pages.PAGE_2">
            <v-container max-width="880">
              <v-card-title class="headline pa-0">
                {{ $t('admin.setup.common-settings-for-new-sites') }}
              </v-card-title>
              <AutoForm
                v-model="commonSettings"
                :items="commonSettingsForm"
              />
            </v-container>
            <v-stepper-actions
              :disabled="isSubmitting"
              prev-text="general.back"
              @click:prev="onPrev"
            >
              <template #next>
                <v-btn
                  variant="flat"
                  color="success"
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :text="$t('general.next')"
                  @click="onNext"
                />
              </template>
            </v-stepper-actions>
          </v-stepper-window-item>

          <!-- AI PROVIDERS -->
          <v-stepper-window-item :value="Pages.AI_PROVIDERS">
            <v-container max-width="880">
              <v-card-title class="headline pa-0">
                {{ $t('group.ai-provider-settings.ai-providers') }}
              </v-card-title>
              <v-card-subtitle class="px-0 py-2 text-wrap">
                {{ $t('group.ai-provider-settings.ai-providers-description') }}
              </v-card-subtitle>
              <KhSetupAiHint /> <!-- KH: AI is optional (D83) -->
              <GroupAIProviderSettingsEditor
                v-if="group?.aiProviderSettings"
                v-model="group.aiProviderSettings"
                hide-header
                class="mt-4"
                @create="handleCreateProvider"
                @update="handleUpdateProvider"
                @delete="handleDeleteProvider"
              />
            </v-container>
            <v-stepper-actions
              :disabled="isSubmitting"
              prev-text="general.back"
              @click:prev="onPrev"
            >
              <template #next>
                <v-btn
                  variant="flat"
                  color="success"
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :text="$t('general.next')"
                  @click="onNext"
                />
              </template>
            </v-stepper-actions>
          </v-stepper-window-item>

          <!-- KH: Kochheft's own steps (D83) -->
          <v-stepper-window-item v-for="step in KH_STEPS" :key="step.page" :value="step.page">
            <v-container max-width="880">
              <v-card-title class="headline pa-0 mb-2">
                {{ $t(step.title) }}
              </v-card-title>
              <component :is="step.component" v-if="currentPage === step.page" />
            </v-container>
            <KhSetupActions
              :disabled="isSubmitting"
              :next-text="step.page === Pages.KH_FAMILY && !khFamily.created.length ? 'kh.wizard.later' : undefined"
              @prev="onPrev"
              @next="onKhNext(step.page)"
            />
          </v-stepper-window-item>

          <!-- CONFIRMATION -->
          <v-stepper-window-item :value="Pages.CONFIRM">
            <v-container max-width="880">
              <v-card-title class="headline pa-0">
                {{ $t('general.confirm-how-does-everything-look') }}
              </v-card-title>
              <v-list>
                <template v-for="(item, idx) in confirmationData">
                  <v-list-item
                    v-if="item.display"
                    :key="idx"
                    class="px-0"
                  >
                    <v-list-item-title>{{ item.text }}</v-list-item-title>
                    <v-list-item-subtitle>{{ item.value }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-divider
                    v-if="idx !== confirmationData.length - 1"
                    :key="`divider-${idx}`"
                  />
                </template>
              </v-list>
            </v-container>
            <v-stepper-actions
              :disabled="isSubmitting"
              prev-text="general.back"
              @click:prev="onPrev"
            >
              <template #next>
                <BaseButton
                  create
                  flat
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :icon="$globals.icons.check"
                  :text="$t('general.submit')"
                  @click="onNext"
                />
              </template>
            </v-stepper-actions>
          </v-stepper-window-item>

          <!-- END -->
          <v-stepper-window-item :value="Pages.END">
            <EndPageContent />
            <v-stepper-actions
              :disabled="isSubmitting"
              prev-text="general.back"
              @click:prev="onPrev"
            >
              <template #next>
                <BaseButton
                  flat
                  color="primary"
                  :disabled="isSubmitting"
                  :loading="isSubmitting"
                  :icon="$globals.icons.home"
                  :text="$t('general.home')"
                  @click="onFinish"
                />
              </template>
            </v-stepper-actions>
          </v-stepper-window-item>
        </v-stepper-window>
      </v-stepper>

      <KhSetupPending v-model="pendingOpen" @next="onNext" /> <!-- KH: D83 -->

      <!-- Dialog Language -->
      <LanguageDialog v-model="langDialog" />
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { useDark } from "@vueuse/core";
import { useAdminApi, useUserApi } from "~/composables/api";
import { useLocales } from "~/composables/use-locales";
import { alert } from "~/composables/use-toast";
import { useUserRegistrationForm } from "~/composables/use-users/user-registration-form";
import { useCommonSettingsForm } from "~/composables/use-setup/common-settings-form";
import { useGroupSelf } from "~/composables/use-groups";
import { useAIProviders } from "~/composables/use-ai-providers";
import UserRegistrationForm from "~/components/Domain/User/UserRegistrationForm.vue";
import GroupAIProviderSettingsEditor from "~/components/Domain/Group/GroupAIProviderSettingsEditor.vue";
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";
import KhSetupAddons from "~~/kh/app/components/KhSetupAddons.vue"; // KH: D83
import KhSetupFamily from "~~/kh/app/components/KhSetupFamily.vue"; // KH: D83
import KhSetupCheck from "~~/kh/app/components/KhSetupCheck.vue"; // KH: D83
import { khFamily, pendingCount, resetKhFamily } from "~~/kh/app/composables/use-kh-setup-family"; // KH: D83
import { useKhSetupSummary } from "~~/kh/app/composables/use-kh-setup-summary"; // KH: D83
import { useKhAddonsLoader } from "~~/kh/app/composables/use-kh-addons"; // KH: D83
import { isRerun, seedTasks } from "~~/kh/app/lib/setup-wizard"; // KH: D83
import { useKhOnboarding } from "~~/kh/app/composables/use-kh-onboarding"; // KH: D83
import { WHATS_NEW } from "~~/kh/app/lib/whats-new"; // KH: D83

definePageMeta({
  layout: "blank",
  middleware: ["admin-only"],
});

// ================================================================
// Setup
const i18n = useI18n();
const auth = useMealieAuth();
const userApi = useUserApi();
const adminApi = useAdminApi();

const groupSlug = computed(() => auth.user.value?.groupSlug);

const { group, actions: groupActions } = useGroupSelf();
const { createOne, updateOne, deleteOne } = useAIProviders();

async function handleCreateProvider(data: AIProviderCreate) {
  const result = await createOne(data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-created"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-create-failed"));
  }
}

async function handleUpdateProvider(id: string, data: AIProviderUpdate) {
  const result = await updateOne(id, data);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-updated"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-update-failed"));
  }
}

async function handleDeleteProvider(id: string) {
  const result = await deleteOne(id);
  if (result.data) {
    await groupActions.refresh();
    alert.success(i18n.t("group.ai-provider-settings.provider-deleted"));
  }
  else {
    alert.error(i18n.t("group.ai-provider-settings.provider-delete-failed"));
  }
}
const { locale } = useLocales();
const router = useRouter();
const isSubmitting = ref(false);
const langDialog = ref(false);
const isDark = useDark();

useSeoMeta({
  title: i18n.t("admin.setup.first-time-setup"),
});

enum Pages {
  LANDING = 1,
  USER_INFO = 2,
  PAGE_2 = 3,
  AI_PROVIDERS = 4,
  KH_ADDONS = 5, // KH: Kochheft's own steps (D83)
  KH_FAMILY = 6,
  KH_CHECK = 7,
  CONFIRM = 8,
  END = 9,
}

// KH: the steps Kochheft adds between the AI providers and the summary (D83)
const KH_STEPS = [
  { page: Pages.KH_ADDONS, icon: "tools", title: "kh.nav.addons", component: KhSetupAddons },
  { page: Pages.KH_FAMILY, icon: "group", title: "kh.wizard.family.title", component: KhSetupFamily },
  { page: Pages.KH_CHECK, icon: "clipboardCheck", title: "kh.wizard.check.title", component: KhSetupCheck },
];

// KH: the wizard opened again on an install that was set up before (D83): no account step, and only the settings the
// admin changes are written
const rerun = isRerun(auth.user.value?.email);
const initialPublic = ref(false);
useKhAddonsLoader();
onBeforeUnmount(resetKhFamily); // the temporary passwords are not kept

function getStepperColor(currentPage: Pages, page: Pages) {
  if (currentPage == page) {
    return "info";
  }
  if (currentPage > page) {
    return "success";
  }
  return "";
}

// ================================================================
// Forms
const { accountDetails, credentials } = useUserRegistrationForm();
const { commonSettingsForm } = useCommonSettingsForm();
const commonSettings = ref({
  makeGroupRecipesPublic: false,
  useSeedData: true,
});

const khSummary = useKhSetupSummary(computed(() => group.value?.aiProviderSettings?.providers.length ?? 0)); // KH: D83

const confirmationData = computed(() => {
  return [
    {
      display: !rerun, // KH: no account lines when opened again (D83)
      text: i18n.t("user.email"),
      value: accountDetails.email.value,
    },
    {
      display: !rerun,
      text: i18n.t("user.username"),
      value: accountDetails.username.value,
    },
    {
      display: !rerun,
      text: i18n.t("user.full-name"),
      value: accountDetails.fullName.value,
    },
    {
      display: !rerun,
      text: i18n.t("user.enable-advanced-content"),
      value: accountDetails.advancedOptions.value ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: true,
      text: i18n.t("group.enable-public-access"),
      value: commonSettings.value.makeGroupRecipesPublic ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    {
      display: true,
      text: i18n.t("user-registration.use-seed-data"),
      value: commonSettings.value.useSeedData ? i18n.t("general.yes") : i18n.t("general.no"),
    },
    ...khSummary.value, // KH: add-ons, people, AI (D83)
  ];
});

// KH: an opened-again wizard starts with the privacy the group has now (D83)
onMounted(async () => {
  if (!rerun) return;
  const { data } = await userApi.groups.getOne(auth.user.value!.groupId);
  if (data?.preferences) {
    initialPublic.value = !data.preferences.privateGroup;
    commonSettings.value.makeGroupRecipesPublic = initialPublic.value;
  }
});

// ================================================================
// Page Navigation
const currentPage = ref(Pages.LANDING);

// ================================================================
// Page Submission

async function updateUser() {
  // Note: auth.user is now a ref
  const { response } = await userApi.users.updateOne(auth.user.value!.id, {
    ...auth.user.value,
    email: accountDetails.email.value,
    username: accountDetails.username.value,
    fullName: accountDetails.fullName.value,
    advanced: accountDetails.advancedOptions.value,
  });

  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
  else {
    auth.getSession();
  }
}

async function updatePassword() {
  // Read before updateUser can change it: the account is still identified by its current email at
  // the point we have to sign back in.
  const currentEmail = auth.user.value!.email;
  const newPassword = credentials.password1.value;

  const { response } = await userApi.users.changePassword({
    currentPassword: "MyPassword",
    newPassword,
  });

  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  // Changing the password invalidates this session, and setup has several authenticated steps left,
  // so sign straight back in rather than letting the rest of the wizard 401.
  const formData = new FormData();
  formData.append("username", currentEmail);
  formData.append("password", newPassword);
  formData.append("remember_me", "true");

  try {
    await auth.signIn(formData);
  }
  catch {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function submitRegistration() {
  // we update the password first, then update the user's details
  await updatePassword().then(updateUser);
}

async function updateGroup() {
  // Note: auth.user is now a ref
  const { data } = await userApi.groups.getOne(auth.user.value!.groupId);
  if (!data || !data.preferences) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  const preferences = {
    ...data.preferences,
    privateGroup: !commonSettings.value.makeGroupRecipesPublic,
  };

  const payload = {
    ...data,
    preferences,
  };

  // Note: auth.user is now a ref
  const { response } = await userApi.groups.updateOne(auth.user.value!.groupId, payload);
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function updateHousehold() {
  // Note: auth.user is now a ref
  const { data } = await adminApi.households.getOne(auth.user.value!.householdId);
  if (!data || !data.preferences) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  const preferences = {
    ...data.preferences,
    privateHousehold: !commonSettings.value.makeGroupRecipesPublic,
    recipePublic: commonSettings.value.makeGroupRecipesPublic,
  };

  const payload = {
    ...data,
    preferences,
  };

  // Note: auth.user is now a ref
  const { response } = await adminApi.households.updateOne(auth.user.value!.householdId, payload);
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedFoods() {
  const { response } = await userApi.seeders.foods({ locale: locale.value });
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedUnits() {
  const { response } = await userApi.seeders.units({ locale: locale.value });
  if (!response || response.status !== 200) {
    alert.error(i18n.t("events.something-went-wrong"));
  }
}

async function seedData() {
  // KH: not what the group already has, so an install running the wizard again keeps its lists (D83). Seeding foods
  // also creates the labels (departments) the shopping list tiles need.
  const [foods, units] = await Promise.all([userApi.foods.getAll(1, 1), userApi.units.getAll(1, 1)]);
  const tasks = seedTasks(commonSettings.value.useSeedData, foods.data?.total ?? 0, units.data?.total ?? 0);

  await Promise.all(tasks.map(task => (task === "foods" ? seedFoods() : seedUnits())));
}

async function submitCommonSettings() {
  // KH: an opened-again wizard writes the privacy only when the admin changed it (D83)
  const privacyTouched = !rerun || commonSettings.value.makeGroupRecipesPublic !== initialPublic.value;
  const tasks = [
    ...(privacyTouched ? [updateGroup(), updateHousehold()] : []),
    seedData(),
  ];

  await Promise.all(tasks);
}

async function submitAll() {
  // Not part of the parallel batch: changing the password invalidates the session and establishes a
  // new one, and any request landing in that window would 401 and bounce the admin out of setup.
  if (!rerun) await submitRegistration(); // KH: the account stays as it is when the wizard is opened again (D83)
  // KH: after the new token is set; the first admin gets the tour instead of the news (D83)
  if (!rerun && auth.user.value) await useKhOnboarding().introduceFirstAdmin(auth.user.value.id, WHATS_NEW[0]!.version, i18n.t("events.something-went-wrong"));

  const tasks = [
    submitCommonSettings(),
    // KH: providers and their order are saved as they are made; an opened-again wizard writes nothing more (D83)
    ...(rerun ? [] : [groupActions.updateAIProviderSettings()]),
  ];

  await Promise.all(tasks);
}

async function handleSubmit(page: number) {
  if (isSubmitting.value) {
    return;
  }

  isSubmitting.value = true;
  switch (page) {
    case Pages.USER_INFO:
      if (await accountDetails.validate()) {
        currentPage.value += 1;
      }
      break;
    case Pages.CONFIRM:
      await submitAll();
      currentPage.value += 1;
      break;
    case Pages.END:
      router.push(groupSlug.value ? `/g/${groupSlug.value}` : "/login");
      break;
  }
  isSubmitting.value = false;
}

// ================================================================
// Stepper Navigation Handlers
function onPrev() {
  if (isSubmitting.value) return;
  if (currentPage.value > Pages.LANDING) currentPage.value -= rerun && currentPage.value === Pages.PAGE_2 ? 2 : 1; // KH: D83
}

async function onNext() {
  if (isSubmitting.value) return;
  if (currentPage.value === Pages.USER_INFO) {
    await handleSubmit(Pages.USER_INFO);
    return;
  }
  if (currentPage.value === Pages.CONFIRM) {
    await handleSubmit(Pages.CONFIRM);
    return;
  }
  currentPage.value += rerun && currentPage.value === Pages.LANDING ? 2 : 1; // KH: skips the account step (D83)
}

// KH: typed but not created people are asked about before the wizard moves on (D83)
const pendingOpen = ref(false);
async function onKhNext(page: Pages) {
  if (page === Pages.KH_FAMILY && pendingCount() > 0) pendingOpen.value = true;
  else await onNext();
}

async function onFinish() {
  if (isSubmitting.value) return;
  await handleSubmit(Pages.END);
}
</script>

<style>
.icon-white {
  fill: white;
}

.icon-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  position: relative;
  margin-top: 2.5rem;
}

.icon-divider {
  width: 100%;
  margin-bottom: -2.5rem;
}

.icon-avatar {
  border-color: rgba(0, 0, 0, 0.12);
  border: 2px;
}

.bg-off-white {
  background: #f5f8fa;
}

.v-stepper-item__avatar.v-avatar.v-stepper-item__avatar.v-avatar {
  width: 3rem !important; /** Override inline style :( */
  height: 3rem !important; /** Override inline style :( */
  margin-inline-end: 0; /** reset weird margin */

  .v-icon {
    font-size: 1.4rem;
  }
}

.v-stepper--alt-labels .v-stepper-header .v-divider {
  margin: 48px -42px 0 !important;
}
</style>
