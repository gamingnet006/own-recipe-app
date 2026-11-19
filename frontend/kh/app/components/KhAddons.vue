<!-- KH: the add-ons page's content (D46): the two big areas as cards, the further functions as rows. Everyone sees the
state, only admins (canChange) can change it. Every change is stored at once. -->
<template>
  <div>
    <KhAddonPresets v-if="canChange && !hidePresets" class="mb-6" />

    <h2 class="text-h6 mb-2">
      {{ $t("kh.addons.areas.title") }}
    </h2>
    <v-card v-for="name in AREAS" :key="name" variant="outlined" class="mb-3 pa-4">
      <v-switch
        :data-testid="`addon-${name}`"
        :model-value="khAddons.flags[name]"
        :disabled="!canChange"
        :label="$t(`kh.addons.areas.${name}.title`)"
        color="primary"
        hide-details
        @update:model-value="change(name, $event)"
      />
      <p class="mb-1">
        {{ $t(`kh.addons.areas.${name}.text`) }}
      </p>
      <p class="text-medium-emphasis text-body-2 mb-0">
        {{ $t(`kh.addons.areas.${name}.gone`) }}
      </p>
    </v-card>

    <h2 class="text-h6 mt-6 mb-2">
      {{ $t("kh.addons.items.title") }}
    </h2>
    <v-card v-for="name in ITEMS" :key="name" variant="outlined" class="mb-2 px-4 py-2">
      <v-switch
        :data-testid="`addon-${name}`"
        :model-value="state(name).on"
        :disabled="!canChange || state(name).disabled"
        :label="$t(`kh.addons.items.${name}.title`)"
        color="primary"
        hide-details
        @update:model-value="change(name, $event)"
      />
      <p class="text-body-2 mb-0">
        {{ $t(`kh.addons.items.${name}.text`) }}
      </p>
      <p v-if="state(name).reason" class="text-body-2 text-warning mb-0">
        {{ hint(state(name).reason) }}
      </p>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import KhAddonPresets from "./KhAddonPresets.vue";
import { ADDON_NAMES, type KhAddonName, rowState, type KhRowState } from "../lib/addons";
import { khAddons, saveKhAddons } from "../composables/use-kh-addons";

defineProps<{ canChange: boolean; hidePresets?: boolean }>(); // the setup steps show the presets as cards (D83)

const i18n = useI18n();
const AREAS = ["shopping", "planner"] as const;
const ITEMS = ADDON_NAMES.filter(name => !(AREAS as readonly string[]).includes(name));

const state = (name: KhAddonName) => rowState(name, khAddons.flags, khAddons.unavailable);

/** The hint under a locked row. */
function hint(reason: KhRowState["reason"]): string {
  return reason === "needs-allergens" ? i18n.t("kh.addons.needs-allergens") : i18n.t("kh.addons.unavailable");
}

function change(name: KhAddonName, on: boolean | null) {
  void saveKhAddons({ ...khAddons.flags, [name]: !!on });
}
</script>
