<!-- KH: "Add to shopping list" under the ingredients of the recipe view (D38), with Mealie's dialog, at the amount the
reader set. -->
<template>
  <div class="d-print-none">
    <v-btn
      block
      size="large"
      variant="outlined"
      class="mt-2"
      :prepend-icon="$globals.icons.cartCheck"
      :loading="addAllLoading"
      @click="addAllToList"
    >
      {{ $t("kh.recipe.add-to-list") }}
    </v-btn>
    <RecipeDialogAddToShoppingList
      v-if="shoppingLists"
      v-model="open"
      :recipes="[{ ...recipe, scale }]"
      :shopping-lists="shoppingLists"
      @list-created="addShoppingList"
    />
  </div>
</template>

<script setup lang="ts">
import RecipeDialogAddToShoppingList from "~/components/Domain/Recipe/RecipeDialogAddToShoppingList.vue";
import { useAddToShoppingListDialog } from "~/composables/shopping-list-page/use-add-to-shopping-list-dialog";
import type { Recipe } from "~/lib/api/types/recipe";

defineProps<{ recipe: Recipe; scale: number }>();

const { shoppingLists, open, addAllLoading, addAllToList, addShoppingList } = useAddToShoppingListDialog();
</script>
