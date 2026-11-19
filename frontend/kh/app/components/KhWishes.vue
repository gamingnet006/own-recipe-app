<!-- KH: the household's wishes beside or above the meal planner (D72): tap a wish, then a day chip, and the recipe is
     planned as dinner for that day. A side column on wide screens, a collapsible section on small ones; nothing is
     shown while there are no wishes. -->
<template>
  <v-card v-if="wishes.length" variant="tonal" class="kh-wishes" data-testid="wishes-panel">
    <v-card-title class="d-flex align-center text-subtitle-1">
      {{ $t("kh.wishes.title") }}
      <v-spacer />
      <v-btn
        v-if="!mdAndUp"
        icon
        variant="text"
        size="small"
        :aria-label="$t('kh.wishes.title')"
        :aria-expanded="!collapsed"
        @click="collapsed = !collapsed"
      >
        <v-icon :icon="$globals.icons.chevronDown" :style="collapsed ? undefined : 'transform: rotate(180deg)'" />
      </v-btn>
    </v-card-title>
    <v-card-text v-if="mdAndUp || !collapsed">
      <div v-for="wish in wishes" :key="wish.recipe.id" class="mb-3">
        <v-btn
          variant="text"
          class="text-none px-0 justify-start"
          :aria-expanded="chosen === wish.recipe.id"
          @click="chosen = chosen === wish.recipe.id ? null : wish.recipe.id"
        >
          {{ wish.recipe.name }}
        </v-btn>
        <div class="text-caption text-medium-emphasis">
          {{ joinNames(wishers(wish, ownId, $t("kh.wishes.you")), $t("kh.wishes.and")) }}
        </div>
        <v-chip-group v-if="chosen === wish.recipe.id" column>
          <v-chip v-for="chip in chips" :key="chip.date" :disabled="busy" @click="plan(wish, chip.date)">
            {{ chip.label }}
          </v-chip>
          <span v-if="!chips.length" class="text-caption">{{ $t("kh.wishes.no-day") }}</span>
        </v-chip-group>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useDisplay } from "vuetify";
import { KhWishesApi, type KhWish } from "../lib/api/wishes";
import { dayChips } from "../lib/week-days";
import { joinNames, wishers } from "../lib/wishes";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

const props = defineProps<{ days: Date[] }>();
/** The wish for the recipe was planned: the planner reloads its entries. */
const emit = defineEmits<{ planned: [] }>();

const api = new KhWishesApi(useRequests());
const i18n = useGlobalI18n();
const { mdAndUp } = useDisplay();
const ownId = useMealieAuth().user.value?.id;
const wishes = ref<KhWish[]>([]);
const chosen = ref<string | null>(null);
const collapsed = ref(true);
const busy = ref(false);
const chips = computed(() => dayChips(props.days, i18n.locale.value));

/** Asks the server again; the planner calls it after plans made elsewhere, which may have ended wishes. */
async function reload() {
  const { data } = await api.list();
  wishes.value = data ?? [];
}

async function plan(wish: KhWish, date: string) {
  busy.value = true;
  const { data } = await api.plan(wish.recipe.id, date);
  busy.value = false;
  if (!data) return alert.error(i18n.t("events.something-went-wrong"));
  chosen.value = null;
  alert.success(i18n.t("kh.wishes.planned", { name: wish.recipe.name }));
  await reload();
  emit("planned");
}

defineExpose({ reload });
onMounted(reload);
</script>

<style scoped>
@media (min-width: 960px) {
  .kh-wishes {
    flex: 0 0 260px;
    align-self: flex-start;
  }
}
</style>
