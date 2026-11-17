<!-- KH: the name of the current household at the top of the start page (D52); only for persons with linked accounts,
so everybody else sees no change. -->
<template>
  <p v-if="current" class="text-body-2 text-medium-emphasis mb-2" data-testid="household-badge">
    <v-icon size="small" :icon="$globals.icons.household" />
    {{ $t("kh.accounts.household-of", { name: current.household }) }}
  </p>
</template>

<script setup lang="ts">
import { useKhAccounts } from "../composables/use-kh-accounts";

const { current, load } = useKhAccounts();
onMounted(load);
</script>
