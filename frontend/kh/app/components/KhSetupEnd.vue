<!-- KH: two more buttons on the wizard's last page (D83): set up this device, and the notifications. -->
<template>
  <div class="d-flex flex-wrap ga-2 justify-center">
    <v-btn :to="SETUP_PATH" color="primary" :prepend-icon="$globals.icons.cellphone">
      {{ $t("kh.wizard.end.device") }}
    </v-btn>
    <v-btn :to="NOTIFICATIONS_PATH" variant="tonal" :prepend-icon="$globals.icons.bellOutline">
      {{ $t("kh.wizard.end.notifications") }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { SETUP_PATH } from "../lib/device-setup";

const { $globals } = useNuxtApp();
const NOTIFICATIONS_PATH = "/mitteilungen";
</script>
