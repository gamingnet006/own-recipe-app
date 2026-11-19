<!-- KH: the shopping page with tiles (D60): a Mealie shopping list per store; red tiles for what is missing, bought
items to put back, and all foods by department of the store. Tap a red tile = bought, hold = details. -->
<template>
  <v-container class="kh-shop pb-12">
    <div class="kh-shop__head">
      <div class="d-flex align-center ga-2">
        <v-btn :icon="$globals.icons.menu" variant="tonal" :aria-label="$t('kh.shopping.stores')" @click="drawer = true" />
        <h1 class="text-h6 font-weight-bold flex-grow-1 text-truncate">
          {{ list?.name ?? $t("kh.nav.shopping") }}
        </h1>
        <v-btn
          v-if="list"
          :icon="$globals.icons.shareVariant"
          variant="tonal"
          :aria-label="$t('kh.share.menu')"
          @click="shareList(list.name ?? '', items)"
        />
      </div>
      <v-text-field
        v-if="list"
        v-model="search"
        :placeholder="$t('kh.shopping.search')"
        variant="solo-filled"
        flat
        hide-details
        class="mt-2"
        autocomplete="off"
        @keydown.enter="addFromSearch"
      />
    </div>

    <template v-if="list">
      <h2 class="kh-shop__title">
        {{ $t("kh.shopping.to-buy") }}
      </h2>
      <div v-if="open.length" class="kh-shop__grid">
        <KhShopTile
          v-for="item in shownOpen"
          :key="item.id"
          variant="list"
          :name="itemTitle(item, units)"
          :emoji="emojiOf(item)"
          :detail="detailOf(item)"
          :badge="badgeOf(item)"
          @press="buy(item)"
          @hold="sheetId = item.id"
        />
      </div>
      <p v-else class="text-medium-emphasis py-3">
        {{ $t("kh.shopping.empty") }}
      </p>

      <template v-if="recent.length && !search">
        <h2 class="kh-shop__title">
          {{ $t("kh.shopping.recent") }}
        </h2>
        <div class="kh-shop__grid">
          <KhShopTile
            v-for="item in recent"
            :key="item.id"
            variant="done"
            :name="itemTitle(item, units)"
            :emoji="emojiOf(item)"
            @press="uncheck(item)"
          />
        </div>
      </template>

      <template v-for="department in shownDepartments" :key="department.labelId ?? department.name">
        <h2 class="kh-shop__title">
          {{ department.name }}
        </h2>
        <div class="kh-shop__grid">
          <KhShopTile
            v-for="tile in visibleTiles(department)"
            :key="tile.name"
            :variant="openItemOf(tile) ? 'list' : 'catalog'"
            :name="tile.name"
            :emoji="tile.emoji"
            @press="tapTile(tile)"
          />
        </div>
        <v-btn
          v-if="!search && department.tiles.length > TILES_PER_DEPARTMENT"
          variant="text"
          size="small"
          class="mt-1"
          @click="toggleAll(department.name)"
        >
          {{ expanded.has(department.name)
            ? $t("kh.shopping.show-fewer")
            : $t("kh.shopping.show-all", { n: department.tiles.length }) }}
        </v-btn>
      </template>

      <template v-if="newName">
        <h2 class="kh-shop__title">
          {{ $t("kh.shopping.new") }}
        </h2>
        <div class="kh-shop__grid">
          <KhShopTile variant="new" :name="newName" :detail="$t('kh.shopping.write-down')" @press="addFromSearch" />
        </div>
      </template>

      <p class="mt-8 text-caption">
        <NuxtLink :to="{ path: `/shopping-lists/${list.id}`, query: { klassisch: '1' } }">
          {{ $t("kh.shopping.classic") }}
        </NuxtLink>
      </p>
    </template>

    <v-progress-linear v-else-if="!ready" indeterminate class="mt-6" />

    <v-navigation-drawer v-model="drawer" temporary location="left" width="280">
      <v-list>
        <v-list-subheader>{{ $t("kh.shopping.stores") }}</v-list-subheader>
        <v-list-item
          v-for="entry in lists"
          :key="entry.id"
          :title="entry.name ?? ''"
          :active="entry.id === list?.id"
          @click="openList(entry.id)"
        />
        <v-list-item
          :prepend-icon="$globals.icons.createAlt"
          :title="$t('kh.shopping.add-store')"
          class="text-primary"
          @click="pickerOpen = true"
        />
      </v-list>
    </v-navigation-drawer>

    <KhStorePicker v-model="pickerOpen" @pick="createStore" />
    <KhShopSheet
      :item="sheetItem"
      :units="units"
      :recipes="recipes"
      @change="change"
      @quantity="setQuantity"
      @remove="removeItem"
      @close="sheetId = null"
    />
    <v-snackbar v-model="undoOpen" :timeout="4000">
      {{ $t("kh.shopping.bought", { name: undoName }) }}
      <template #actions>
        <v-btn variant="text" @click="undo">
          {{ $t("kh.shopping.undo") }}
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import type { ShoppingListItemOut } from "~/lib/api/types/household";
import { useEventListener, useIntervalFn } from "@vueuse/core";
import { useKhShareList } from "../composables/use-kh-share-list";
import { useKhShopping } from "../composables/use-kh-shopping";
import { URGENCY, itemDetail, itemTitle, splitLeadingAmount, urgencyOf } from "../lib/shopping-items";
import type { StorePreset } from "../lib/shopping-stores";
import { type Department, type Tile, filterCatalog, itemForTile, tileEmoji } from "../lib/shopping-tiles";

const TILES_PER_DEPARTMENT = 12;
const REFRESH_MS = 30_000;

const i18n = useI18n();
const route = useRoute();
const { shareList } = useKhShareList();
const {
  lists, list, ready, items, open, recent, recipes, departments, units,
  start, select, reload, change, check, uncheck, remove, addTile, addTyped, setQuantity, createStore: makeStore,
} = useKhShopping();

const search = ref("");
const drawer = ref(false);
const pickerOpen = ref(false);
const sheetId = ref<string | null>(null);
const expanded = ref(new Set<string>());
const undoOpen = ref(false);
const undoItem = ref<ShoppingListItemOut | null>(null);

const sheetItem = computed(() => items.value.find(item => item.id === sheetId.value) ?? null);
const undoName = computed(() => (undoItem.value ? itemTitle(undoItem.value, units.value) : ""));
// "2 Liter Milch" in the search field: the tiles are filtered by the article, the amount goes with a tapped tile
const typed = computed(() => splitLeadingAmount(search.value, units.value));
const query = computed(() => typed.value.rest.toLowerCase());
const shownOpen = computed(() => (query.value ? open.value.filter(item => itemTitle(item, units.value).toLowerCase().includes(query.value)) : open.value));
const shownDepartments = computed(() => filterCatalog(departments.value, typed.value.rest));
// a text whose article is no tile yet can be written down as typed
const newName = computed(() => {
  const name = search.value.trim();
  const known = departments.value.some(department => department.tiles.some(tile => tile.name.toLowerCase() === query.value));
  return query.value && !known ? name.charAt(0).toUpperCase() + name.slice(1) : "";
});

const openItemOf = (tile: Tile) => itemForTile(tile, open.value);
const emojiOf = (item: ShoppingListItemOut) => tileEmoji(itemTitle(item, units.value), item.label?.name ?? "");
const detailOf = (item: ShoppingListItemOut) =>
  itemDetail(item, units.value, recipes.value, name => i18n.t("kh.shopping.from-recipe-short", { name }));
const badgeOf = (item: ShoppingListItemOut) => URGENCY.find(entry => entry.key === urgencyOf(item))?.icon;

function visibleTiles(department: Department) {
  return query.value || expanded.value.has(department.name) ? department.tiles : department.tiles.slice(0, TILES_PER_DEPARTMENT);
}

function toggleAll(name: string) {
  const next = new Set(expanded.value);
  if (!next.delete(name)) next.add(name);
  expanded.value = next;
}

/** Checks the item off and offers to undo it for a few seconds. */
async function buy(item: ShoppingListItemOut) {
  undoItem.value = item;
  undoOpen.value = true;
  await check(item);
}

async function undo() {
  undoOpen.value = false;
  if (undoItem.value) await uncheck(undoItem.value);
}

/** Writes a tile down with the amount typed in the search, and opens its details; one already on the list just opens. */
async function tapTile(tile: Tile) {
  const { quantity, unit } = typed.value;
  const item = await addTile(tile, quantity ? { quantity, unit } : undefined);
  search.value = "";
  if (item) sheetId.value = item.id;
}

/** Enter in the search field or the tile "write down": the server reads the line, then it is on the list. */
async function addFromSearch() {
  const text = search.value.trim();
  if (!text) return;
  search.value = "";
  const item = await addTyped(text);
  if (item) sheetId.value = item.id;
}

async function removeItem(item: ShoppingListItemOut) {
  sheetId.value = null;
  await remove(item);
}

async function openList(id: string) {
  drawer.value = false;
  await select(id);
}

async function createStore(store: StorePreset) {
  pickerOpen.value = false;
  drawer.value = false;
  await makeStore(store.name, store.kind);
}

// set up at once, not after the list has loaded, so leaving the page early leaves nothing behind
const refresh = () => {
  if (document.visibilityState === "visible") void reload(true);
};
useEventListener(document, "visibilitychange", refresh);
useIntervalFn(refresh, REFRESH_MS);

onMounted(async () => {
  await start(typeof route.query.liste === "string" ? route.query.liste : null);
  if (!list.value) pickerOpen.value = true;
});

// the manifest of this page makes "Add to Home Screen" a shopping app of its own
useHead({ link: [{ rel: "manifest", href: "/einkauf.webmanifest", key: "manifest", crossorigin: "use-credentials" }] });
</script>

<style scoped>
.kh-shop {
  max-width: 560px;
}

.kh-shop__head {
  position: sticky;
  top: 48px;
  z-index: 5;
  padding: 8px 0;
  background: rgb(var(--v-theme-background));
}

.kh-shop__title {
  margin: 22px 0 10px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.kh-shop__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 8px;
}
</style>
