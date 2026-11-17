<template>
  <div>
    <KhHouseholdBadge /> <!-- KH: current household, only with linked accounts (D52) -->
    <RecipeExplorerPage />
  </div>
</template>

<script setup lang="ts">
import RecipeExplorerPage from "~/components/Domain/Recipe/RecipeExplorerPage/RecipeExplorerPage.vue";
</script>
