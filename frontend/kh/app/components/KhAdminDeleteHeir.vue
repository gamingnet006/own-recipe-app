<!-- KH: in Mealie's admin dialog for deleting a user (D78): who takes over the recipes and lists, preset with the
     person the server would pick, and what is deleted. -->
<template>
  <div v-if="userId" class="mt-4">
    <v-select
      v-if="options.length"
      v-model="heirId"
      :items="options"
      item-title="name"
      item-value="id"
      :label="$t('kh.account-delete.admin-heir')"
      hide-details
      class="mb-2"
    />
    <p class="text-body-2">
      {{ $t("kh.account-delete.admin-note") }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { heirOptions } from "../lib/account-delete";
import { KhAccountsApi } from "../lib/api/accounts";
import { useRequests } from "~/composables/api/api-client";

const props = defineProps<{
  userId: string;
  users: { id: string; householdId: string; fullName?: string | null; username?: string | null }[];
}>();
const heirId = defineModel<string | null>({ default: null });
const api = new KhAccountsApi(useRequests());

const options = computed(() =>
  heirOptions(props.users, props.userId).map(user => ({ id: user.id, name: user.fullName || user.username || "" })),
);

// The server's own choice is the preset, so the rule for it exists in one place only.
watch(() => props.userId, async (id) => {
  heirId.value = null;
  if (id) {
    const { data } = await api.heir(id);
    heirId.value = data?.id ?? null;
  }
}, { immediate: true });
</script>
