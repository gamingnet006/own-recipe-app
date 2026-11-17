<!-- KH: "More > Households" for admins (D52): who may switch between which households. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.households") }}
      </template>
      {{ $t("kh.accounts.admin.description") }}
    </BasePageTitle>
    <KhHouseholds />
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ["auth", "group-only", "admin-only"],
});

const i18n = useI18n();
useSeoMeta({ title: i18n.t("kh.nav.households") });
</script>
