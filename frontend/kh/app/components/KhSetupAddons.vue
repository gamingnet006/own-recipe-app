<!-- KH: the setup wizard's "Zusatzfunktionen" step (D83): the three presets of D46 as big choice cards, below them the
individual switches of the add-ons page (KhAddons). Every choice is stored at once, like on that page. -->
<template>
  <div>
    <p class="mb-4">
      {{ $t("kh.wizard.addons.intro") }}
    </p>
    <div class="d-flex flex-column ga-3 mb-6">
      <v-card
        v-for="preset in PRESETS"
        :key="preset"
        :variant="current === preset ? 'flat' : 'outlined'"
        :color="current === preset ? 'primary' : undefined"
        class="pa-4"
        :data-testid="`preset-${preset}`"
        @click="choose(preset)"
      >
        <div class="d-flex align-center">
          <v-icon class="me-3" size="large">
            {{ current === preset ? $globals.icons.checkboxMarkedCircle : $globals.icons[ICONS[preset]] }}
          </v-icon>
          <div>
            <div class="text-h6">
              {{ $t(`kh.addons.presets.${preset}`) }}
            </div>
            <div class="text-body-2">
              {{ $t(`kh.wizard.addons.${preset}`) }}
            </div>
          </div>
        </div>
      </v-card>
    </div>
    <KhAddons can-change hide-presets />
  </div>
</template>

<script setup lang="ts">
import KhAddons from "./KhAddons.vue";
import { applyPreset, currentPreset, type KhPreset } from "../lib/addons";
import { khAddons, saveKhAddons } from "../composables/use-kh-addons";

const { $globals } = useNuxtApp();
const PRESETS: KhPreset[] = ["recipes", "shopping", "planner"];
// Mealie icons ($globals.icons) of the cards that are not chosen
const ICONS = { recipes: "silverwareForkKnife", shopping: "formatListCheck", planner: "calendarMultiselect" } as const;
const current = computed(() => currentPreset(khAddons.flags));

function choose(preset: KhPreset) {
  void saveKhAddons(applyPreset(khAddons.flags, preset));
}
</script>
