<template>
  <div>
    <KhHouseholdBadge /> <!-- KH: current household, only with linked accounts (D52) -->
    <KhTour v-model="showTour" @done="onTourDone" /> <!-- KH: first-sign-in tour (D59) -->
    <KhCookedRows v-if="isOwnGroup" /> <!-- KH: often cooked and not cooked for long (D67), only on the own group's page; above the list, which scrolls on and on -->
    <RecipeExplorerPage />
  </div>
</template>

<script setup lang="ts">
import RecipeExplorerPage from "~/components/Domain/Recipe/RecipeExplorerPage/RecipeExplorerPage.vue";
import { khOnboarding, useKhOnboarding } from "~~/kh/app/composables/use-kh-onboarding"; // KH: tour (D59)
import { useLoggedInState } from "~/composables/use-logged-in-state"; // KH: D67
import { shouldShowTour } from "~~/kh/app/lib/tour"; // KH: D59

// KH: the first-sign-in tour (D59); the route guard has loaded the status before the page shows
const i18n = useI18n();
const { isOwnGroup } = useLoggedInState(); // KH: D67
const showTour = ref(shouldShowTour(khOnboarding.status, !!useMealieAuth().user.value));
const onTourDone = () => useKhOnboarding().finishTour(i18n.t("events.something-went-wrong"));
</script>
