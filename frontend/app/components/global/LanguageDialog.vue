<template>
  <BaseDialog
    v-model="modelValue"
    bottom-sheet
    :icon="$globals.icons.translate"
    :title="$t('language-dialog.choose-language')"
  >
    <v-card-text>
      <!-- KH: only Deutsch and English, no percentages; the choice is kept on the account (wave 2) -->
      <KhLanguageButtons :model-value="locale" @choose="onLocaleSelect" />
    </v-card-text>
  </BaseDialog>
</template>

<script setup lang="ts">
import { useLocales } from "~/composables/use-locales";
import { chooseKhLocale } from "~~/kh/app/composables/use-kh-locale"; // KH: wave 2
import type { KhLocale } from "~~/kh/app/lib/locale"; // KH: wave 2

const modelValue = defineModel<boolean>({ default: () => false });

const { locale } = useLocales();
const auth = useMealieAuth(); // KH: wave 2

const onLocaleSelect = (value: KhLocale) => {
  chooseKhLocale(value, !!auth.user.value); // KH: shown at once, kept on the account when signed in
};

watch(locale, () => {
  modelValue.value = false; // Close dialog when locale changes
});
</script>
