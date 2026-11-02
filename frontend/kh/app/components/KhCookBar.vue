<!-- KH: "Start cooking" fixed at the bottom of the recipe view, above the bar (D38). It sits outside the recipe's card,
so nothing on the page scrolls over it and catches the tap. -->
<template>
  <v-footer app class="d-print-none pa-3">
    <v-btn block size="large" color="primary" :prepend-icon="$globals.icons.potSteam" @click="$emit('cook')">
      {{ $t("kh.recipe.cook") }}
    </v-btn>
  </v-footer>
</template>

<script setup lang="ts">
defineEmits<{ cook: [] }>();
</script>
