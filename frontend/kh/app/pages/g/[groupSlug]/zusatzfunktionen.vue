<!-- KH: "More > Add-ons" (D46): which functions this household uses. Everyone reads, admins change. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.nav.addons") }}
      </template>
      {{ $t("kh.addons.description") }}
    </BasePageTitle>
    <KhAddons :can-change="!!auth.user.value?.admin" />
  </v-container>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const auth = useMealieAuth();
useSeoMeta({ title: i18n.t("kh.nav.addons") });
</script>
