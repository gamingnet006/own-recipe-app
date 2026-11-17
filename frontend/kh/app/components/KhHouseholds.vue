<!-- KH: the admin's page content for switching households (D52): every person with their households, "give access to
another household" with a choice of all households of all groups, and "remove access" for linked accounts. -->
<template>
  <div>
    <v-card v-for="person in people" :key="person.userId" variant="outlined" class="mb-3 pa-4">
      <h2 class="text-h6">
        {{ person.fullName }}
      </h2>
      <v-list density="compact" class="py-0">
        <v-list-item
          v-for="(account, index) in person.accounts"
          :key="account.userId"
          :title="`${account.household} · ${account.group}`"
          :subtitle="index === 0 ? $t('kh.accounts.admin.main') : undefined"
        >
          <template v-if="index > 0" #append>
            <v-btn variant="text" size="small" :data-testid="`unlink-${account.userId}`" @click="remove(account.userId)">
              {{ $t("kh.accounts.admin.remove") }}
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-select
        v-model="chosen[person.userId]"
        :items="freeHouseholds(person)"
        :label="$t('kh.accounts.admin.add')"
        item-title="title"
        item-value="id"
        hide-details
        class="mt-3"
      >
        <template #append>
          <v-btn color="primary" :disabled="!chosen[person.userId]" @click="add(person.userId)">
            {{ $t("kh.accounts.admin.give") }}
          </v-btn>
        </template>
      </v-select>
    </v-card>
    <p v-if="!people.length" class="text-medium-emphasis">
      {{ $t("kh.accounts.admin.none") }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { type KhPerson, KhAccountsApi } from "../lib/api/accounts";
import { useAdminApi, useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

const i18n = useI18n();
const accountsApi = new KhAccountsApi(useRequests());
const people = ref<KhPerson[]>([]);
const households = ref<{ id: string; title: string }[]>([]);
const chosen = ref<Record<string, string | undefined>>({});

/** Loads the persons and all households of all groups. */
async function load() {
  const [{ data: found }, { data: all }] = await Promise.all([accountsApi.people(), useAdminApi().households.getAll(1, -1)]);
  people.value = found ?? [];
  households.value = (all?.items ?? []).map(h => ({ id: h.id, title: `${h.name} · ${h.group}` }));
}
onMounted(load);

/** The households the person has no account in yet. */
function freeHouseholds(person: KhPerson) {
  const taken = new Set(person.accounts.map(account => account.householdId));
  return households.value.filter(household => !taken.has(household.id));
}

/** Runs one change, tells the result, and reloads the list. */
async function change(request: Promise<{ error: unknown }>, message: string) {
  const { error } = await request;
  if (error) alert.error(i18n.t("events.something-went-wrong"));
  else alert.success(message);
  await load();
}

async function add(userId: string) {
  await change(accountsApi.link(userId, chosen.value[userId] as string), i18n.t("kh.accounts.admin.added"));
  chosen.value[userId] = undefined;
}

async function remove(userId: string) {
  await change(accountsApi.unlink(userId), i18n.t("kh.accounts.admin.removed"));
}
</script>
