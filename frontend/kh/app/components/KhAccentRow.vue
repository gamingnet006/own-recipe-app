<!-- KH: the settings row "Farbe" (wave 2): the person's own colour, or the installation's; shown at once and kept on
the account, so every device follows. -->
<template>
  <v-list-item :prepend-icon="$globals.icons.palette" :title="$t('kh.accent.title')">
    <p class="text-body-2 text-medium-emphasis text-wrap mb-3">
      {{ $t("kh.accent.hint") }}
    </p>
    <KhAccentChoice :model-value="khSidebar.accent" with-installation @update:model-value="saveKhAccent" />
  </v-list-item>
</template>

<script setup lang="ts">
import { khSidebar, saveKhAccent } from "../composables/use-kh-sidebar";
</script>
