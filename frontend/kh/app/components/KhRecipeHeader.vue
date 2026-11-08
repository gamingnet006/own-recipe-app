<!-- KH: the calm head of the recipe view (D38): the photo with back, favorite and the menu ⋯ of Mealie's actions, the
title with its origin, the times as tiles and the amount with − and +. -->
<template>
  <div class="d-print-none">
    <div class="kh-photo" :class="{ 'kh-photo--empty': !showImage }">
      <v-img
        v-if="showImage"
        :src="imageUrl"
        :alt="recipe.name"
        cover
        height="100%"
        @error="imageFailed = true"
      />
      <v-icon v-else :icon="$globals.icons.silverwareForkKnife" size="32" class="opacity-60" />
      <div class="kh-photo__bar">
        <v-btn
          icon
          :size="44"
          variant="flat"
          color="surface"
          :aria-label="$t('general.back')"
          @click="back"
        >
          <v-icon :icon="$globals.icons.arrowLeftBold" />
        </v-btn>
        <v-spacer />
        <div v-if="isOwnGroup" class="kh-photo__round">
          <RecipeFavoriteBadge :recipe-id="recipe.id" show-always variant="text" :size="44" />
        </div>
        <!-- d-print-none: "Print" runs while the menu is still open -->
        <v-menu
          location="bottom end"
          content-class="d-print-none"
          :eager="menuLoaded"
          @update:model-value="menuLoaded = true"
        >
          <template #activator="{ props: menuProps }">
            <v-btn
              v-bind="menuProps"
              icon
              :size="44"
              variant="flat"
              color="surface"
              :aria-label="$t('kh.recipe.actions')"
            >
              <v-icon :icon="$globals.icons.dotsHorizontal" />
            </v-btn>
          </template>
          <v-card min-width="240">
            <v-list density="compact">
              <v-list-item
                v-if="canEditRecipe"
                :prepend-icon="$globals.icons.edit"
                :title="$t('general.edit')"
                @click="$emit('edit')"
              />
              <v-list-item
                v-if="isOwnGroup"
                :prepend-icon="$globals.icons.chefHat"
                :title="$t('kh.recipe.mark-cooked')"
                @click="madeThis = true"
              />
              <v-list-item
                v-if="original"
                :prepend-icon="$globals.icons.link"
                :title="$t('kh.drafts.view-original')"
                :href="original"
                target="_blank"
                rel="noopener noreferrer"
              />
            </v-list>
            <!-- Mealie's own actions; "Share" shows only with share links on (KH_SHARE_LINKS) -->
            <RecipeContextMenuContent
              :recipe="recipe"
              :recipe-id="recipe.id"
              :slug="recipe.slug"
              :name="recipe.name"
              :recipe-scale="scale"
              :use-items="menuItems"
              @print="print"
            />
          </v-card>
        </v-menu>
      </div>
    </div>
    <!-- only its "I made this" dialog, opened from the menu; Mealie's "last made" block stays hidden -->
    <RecipeLastMade v-if="isOwnGroup" v-model:dialog="madeThis" :recipe="recipe" class="d-none" />

    <section class="px-4 pt-4">
      <h1 class="text-headline-small font-weight-bold text-wrap">
        {{ recipe.name }}
      </h1>
      <SafeMarkdown v-if="recipe.description" :source="recipe.description" class="mt-2" />
    </section>
    <KhOriginBadge :recipe-id="recipe.id" />
    <p v-if="!online" class="px-4 pt-2 text-body-medium text-medium-emphasis" role="status">
      {{ $t("kh.cook.offline") }}
    </p>

    <div v-if="times.length || base || recipe.recipeYield || hasAmounts" class="pa-4 d-flex flex-column ga-4">
      <div v-if="times.length" class="kh-times">
        <v-card v-for="time in times" :key="time.key" variant="outlined" class="px-1 py-2 text-center">
          <div class="text-title-medium font-weight-bold">
            {{ time.value }}
          </div>
          <div class="text-body-small text-medium-emphasis">
            {{ $t(`recipe.${time.key}-time`) }}
          </div>
        </v-card>
      </div>

      <v-card v-if="base || recipe.recipeYield" variant="outlined" class="pa-3 d-flex align-center ga-3">
        <h2 class="text-title-medium font-weight-bold">
          {{ $t("kh.recipe.amount") }}
        </h2>
        <v-spacer />
        <v-btn
          v-if="canScale"
          icon
          :size="44"
          variant="outlined"
          :disabled="shown <= 1"
          :aria-label="$t('kh.recipe.fewer')"
          @click="step(-1)"
        >
          <v-icon :icon="$globals.icons.minus" />
        </v-btn>
        <div aria-live="polite" class="text-center">
          <!-- eslint-disable-next-line vue/no-v-html -- Mealie's amount, numbers only, with <sup>/<sub> fractions -->
          <span v-if="base" class="text-title-large font-weight-bold" v-html="amount" />
          {{ label }}
        </div>
        <v-btn
          v-if="canScale"
          icon
          :size="44"
          variant="outlined"
          :aria-label="$t('kh.recipe.more')"
          @click="step(1)"
        >
          <v-icon :icon="$globals.icons.createAlt" />
        </v-btn>
      </v-card>
      <!-- the three ways to scale, and the hint on times (D39, A3, A5) -->
      <div v-if="hasAmounts" class="d-flex flex-column ga-2">
        <v-btn variant="tonal" :prepend-icon="$globals.icons.swapHorizontal" @click="sheet = true">
          {{ $t("kh.amounts.scale.title") }}
        </v-btn>
        <p v-if="timeHint(scale)" class="text-body-medium text-medium-emphasis">
          {{ $t("kh.recipe.time-hint") }}
        </p>
      </div>
      <KhScaleSheet v-if="hasAmounts" v-model="sheet" v-model:scale="scale" :recipe="recipe" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useOnline } from "@vueuse/core";
import { recipeTimes, scaleBase, scaleLabel, scalesAmounts, sourceLink, stepScale } from "../composables/use-kh-recipe";
import { timeHint } from "../lib/amounts";
import KhOriginBadge from "./KhOriginBadge.vue";
import KhScaleSheet from "./KhScaleSheet.vue";
import RecipeContextMenuContent from "~/components/Domain/Recipe/RecipeContextMenu/RecipeContextMenuContent.vue";
import RecipeFavoriteBadge from "~/components/Domain/Recipe/RecipeFavoriteBadge.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import { useStaticRoutes, useUserApi } from "~/composables/api";
import { usePageState, usePageUser } from "~/composables/recipe-page/shared-state";
import { useRecipePermissions } from "~/composables/recipes";
import { useScaledAmount } from "~/composables/recipes/use-scaled-amount";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import type { HouseholdSummary } from "~/lib/api/types/household";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { Recipe } from "~/lib/api/types/recipe";

const props = defineProps<{ recipe: NoUndefinedField<Recipe> }>();
const online = useOnline();
defineEmits<{ edit: [] }>();
const scale = defineModel<number>("scale", { required: true });

const i18n = useI18n();
const route = useRoute();
const router = useRouter();
const { isOwnGroup } = useLoggedInState();
const { recipeImage } = useStaticRoutes();
const { imageKey } = usePageState(props.recipe.slug);
const { user } = usePageUser();

// The menu holds Mealie's dialogs, so once opened it stays mounted, as in Mealie's RecipeContextMenu
const menuLoaded = ref(false);
const madeThis = ref(false);
const menuItems = { edit: false, mealplanner: true, print: true, share: true, delete: true, download: false,
  duplicate: false, shoppingList: false, printPreferences: false, recipeActions: true };

// Who may edit, as in Mealie's RecipePageHeader: the recipe's household decides for other households' recipes
const recipeHousehold = ref<HouseholdSummary>();
if (user) {
  useUserApi().households.getOne(props.recipe.householdId).then(({ data }) => {
    recipeHousehold.value = data || undefined;
  });
}
const { canEditRecipe } = useRecipePermissions(props.recipe, recipeHousehold, user);

const imageFailed = ref(false);
const imageUrl = computed(() => recipeImage(props.recipe.id, props.recipe.image, imageKey.value));
const showImage = computed(() => !!props.recipe.image && !imageFailed.value);
watch(imageUrl, () => {
  imageFailed.value = false;
});

const original = computed(() => sourceLink(props.recipe.orgURL));
const times = computed(() => recipeTimes(props.recipe, i18n.locale.value));
const base = computed(() => scaleBase(props.recipe));
const hasAmounts = computed(() => scalesAmounts(props.recipe));
const canScale = computed(() => base.value > 0 && hasAmounts.value);
const sheet = ref(false);
const scaled = computed(() => useScaledAmount(base.value, scale.value));
const shown = computed(() => scaled.value.scaledAmount);
const amount = computed(() => scaled.value.scaledAmountDisplay);
const label = computed(() => scaleLabel(props.recipe, shown.value, (key, count) => i18n.t(key, count)));

/** One whole piece or serving more or less. */
function step(delta: 1 | -1) {
  scale.value = stepScale(base.value, scale.value, delta);
}

/** Back where the reader came from, or to the recipes when the page was opened directly. */
function back() {
  if (window.history.state?.back) router.back();
  else router.push(`/g/${route.params.groupSlug as string}`);
}

/** The recipe card (D43) with the servings chosen here, instead of printing this page. */
function print() {
  const servings = Number(((props.recipe.recipeServings || 0) * scale.value).toFixed(3));
  router.push({ path: `/g/${route.params.groupSlug as string}/kochbuch/rezept/${props.recipe.slug}`, query: servings ? { servings } : {} });
}
</script>

<style scoped>
.kh-photo {
  position: relative;
  height: 240px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.06);
}
.kh-photo--empty {
  height: 96px;
}
@media (min-width: 600px) {
  .kh-photo:not(.kh-photo--empty) {
    height: 320px;
  }
}
.kh-photo__bar {
  position: absolute;
  inset: 12px 12px auto;
  display: flex;
  gap: 8px;
}
.kh-photo__round {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--v-theme-surface));
}
/* the heart in the look's accent, readable on the light and the dark circle; Mealie colors it secondary */
.kh-photo__round :deep(.v-icon) {
  color: rgb(var(--v-theme-primary)) !important;
}
.kh-times {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
</style>
