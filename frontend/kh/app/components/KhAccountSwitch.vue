<!-- KH: the dialog of "More > Switch household" (D52): the person's accounts as "household · group", the current one
checked. A tap signs in to that account. -->
<template>
  <v-dialog v-model="open" max-width="420">
    <v-card :title="$t('kh.accounts.switch')" :subtitle="$t('kh.accounts.switch-hint')">
      <v-list>
        <v-list-item
          v-for="account in accounts"
          :key="account.userId"
          :title="`${account.household} · ${account.group}`"
          :append-icon="account.current ? $globals.icons.check : undefined"
          :aria-current="account.current"
          @click="account.current ? (open = false) : switchTo(account.userId)"
        />
      </v-list>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { useKhAccounts } from "../composables/use-kh-accounts";

const open = defineModel<boolean>({ required: true });
const { accounts, switchTo } = useKhAccounts();
</script>
