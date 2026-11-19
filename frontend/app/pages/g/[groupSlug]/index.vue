<template>
  <div>
    <KhHouseholdBadge /> <!-- KH: current household, only with linked accounts (D52) -->
    <KhTour v-model="showTour" @done="onTourDone" /> <!-- KH: first-sign-in tour (D59) -->
    <RecipeExplorerPage />
  </div>
</template>

<script setup lang="ts">
import RecipeExplorerPage from "~/components/Domain/Recipe/RecipeExplorerPage/RecipeExplorerPage.vue";
import { khOnboarding, useKhOnboarding } from "~~/kh/app/composables/use-kh-onboarding"; // KH: tour (D59)
import { shouldShowTour } from "~~/kh/app/lib/tour"; // KH: D59

// KH: the first-sign-in tour (D59); the route guard has loaded the status before the page shows
const i18n = useI18n();
const showTour = ref(shouldShowTour(khOnboarding.status, !!useMealieAuth().user.value));
const onTourDone = () => useKhOnboarding().finishTour(i18n.t("events.something-went-wrong"));
</script>
