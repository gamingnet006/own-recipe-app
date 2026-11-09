<!-- KH: "How do you want to use Kochheft?" (D46, G1): three presets that only set the two big switches. Used on the
add-ons page and in the first-start list of the system check. -->
<template>
  <div>
    <h3 class="text-subtitle-1 font-weight-bold mb-1">
      {{ $t("kh.addons.presets.title") }}
    </h3>
    <div class="d-flex flex-wrap ga-2">
      <v-btn
        v-for="preset in PRESETS"
        :key="preset"
        :variant="current === preset ? 'flat' : 'tonal'"
        color="primary"
        @click="choose(preset)"
      >
        {{ $t(`kh.addons.presets.${preset}`) }}
      </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { applyPreset, currentPreset, type KhPreset } from "../lib/addons";
import { khAddons, saveKhAddons } from "../composables/use-kh-addons";

const PRESETS: KhPreset[] = ["recipes", "shopping", "planner"];
const current = computed(() => currentPreset(khAddons.flags));

function choose(preset: KhPreset) {
  void saveKhAddons(applyPreset(khAddons.flags, preset));
}
</script>
