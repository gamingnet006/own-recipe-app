<!-- KH: the Kochheft icon drawn in the accent colour (wave 2): inline SVG on the theme's colours, so it follows the
chosen colour at once. An own branding logo, when one is configured, is shown as the picture it is. -->
<template>
  <v-img v-if="$appInfo.brandingLogoUrl" :src="$appInfo.brandingLogoUrl" :width="size" :height="size" />
  <svg
    v-else
    class="kh-logo"
    :width="size"
    :height="size"
    viewBox="0 0 76 76"
    aria-hidden="true"
  >
    <rect
      x="14"
      y="10"
      width="44"
      height="56"
      rx="6"
      class="kh-logo-page"
      stroke-width="3.2"
      stroke-linejoin="round"
    />
    <path
      d="M22 10v56M30 26h16M30 34h16M30 42h10"
      fill="none"
      class="kh-logo-line"
      stroke-width="3.2"
      stroke-linecap="round"
    />
    <ellipse cx="52" cy="10" rx="5" ry="6.5" class="kh-logo-fill" />
    <path
      d="M52 16v18"
      fill="none"
      class="kh-logo-line"
      stroke-width="3.2"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 40 });
</script>

<style scoped>
.kh-logo-page {
  fill: rgb(var(--v-theme-kh-hint));
  stroke: rgb(var(--v-theme-primary));
}
.kh-logo-line {
  stroke: rgb(var(--v-theme-primary));
}
.kh-logo-fill {
  fill: rgb(var(--v-theme-primary));
}
</style>
