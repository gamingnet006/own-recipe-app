<!-- KH: the choice System / Light / Dark for this device (use-kh-theme.ts), used in More and on the settings page. -->
<template>
  <v-btn-toggle
    v-model="choice"
    mandatory
    density="compact"
    color="primary"
    variant="outlined"
    divided
    :aria-label="$t('kh.theme.title')"
  >
    <v-btn v-for="value in THEME_CHOICES" :key="value" :value="value" size="small">
      {{ $t(`kh.theme.${value}`) }}
    </v-btn>
  </v-btn-toggle>
</template>

<script setup lang="ts">
import { useKhTheme } from "~~/kh/app/composables/use-kh-theme";
import { THEME_CHOICES } from "~~/kh/app/lib/theme";

const { choice } = useKhTheme();
</script>
