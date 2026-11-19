<template>
  <div>
    <KhHouseholdBadge /> <!-- KH: current household, only with linked accounts (D52) -->
    <KhStartDialogs /> <!-- KH: first-sign-in tour (D59), news (D69) or the new-device question (D68), at most one -->
    <KhCookedRows v-if="isOwnGroup" /> <!-- KH: often cooked and not cooked for long (D67), only on the own group's page; above the list, which scrolls on and on -->
    <RecipeExplorerPage />
  </div>
</template>

<script setup lang="ts">
import RecipeExplorerPage from "~/components/Domain/Recipe/RecipeExplorerPage/RecipeExplorerPage.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state"; // KH: D67

const { isOwnGroup } = useLoggedInState(); // KH: D67
</script>
