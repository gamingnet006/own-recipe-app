<!-- KH: the small "Anpassen" entry at the end of the side menu; it opens the same tick list as the settings page. -->
<template>
  <v-list-item
    :prepend-icon="$globals.icons.edit"
    :title="$t('kh.nav.customize')"
    density="compact"
    @click="open = true"
  />
  <v-dialog v-model="open" max-width="480">
    <v-card>
      <v-card-title>{{ $t("kh.nav.sidebar") }}</v-card-title>
      <v-card-text class="pa-0">
        <KhSidebarChoices />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="open = false">
          {{ $t("general.close") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
const open = ref(false);
</script>
