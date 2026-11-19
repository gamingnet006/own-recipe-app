<!-- KH: the setup wizard's "Familie" step (D83): add the people of the household right here. One card per person to be
created; every created person gets a card with the address, user name and the temporary password, shown only now. -->
<template>
  <div>
    <p class="mb-4">
      {{ $t("kh.wizard.family.intro") }}
    </p>

    <v-card
      v-for="(row, index) in khFamily.rows"
      :key="index"
      variant="outlined"
      class="mb-3 pa-4"
      :data-testid="`family-row-${index}`"
    >
      <v-text-field
        v-model="row.name"
        :label="$t('kh.wizard.family.name')"
        :error-messages="message(index, 'name')"
        autocomplete="off"
        density="comfortable"
        @update:model-value="clearFailure(index)"
      />
      <v-text-field
        v-model="row.username"
        :label="$t('kh.wizard.family.username')"
        :error-messages="message(index, 'username')"
        autocomplete="off"
        autocapitalize="none"
        density="comfortable"
        @update:model-value="clearFailure(index)"
      />
      <v-text-field
        v-model="row.email"
        :label="$t('kh.wizard.family.email')"
        :error-messages="message(index, 'email')"
        type="email"
        autocomplete="off"
        density="comfortable"
        @update:model-value="clearFailure(index)"
      />
      <v-checkbox v-model="row.tour" :label="$t('kh.tour.with-tour')" color="primary" hide-details density="compact" />
      <v-checkbox v-model="row.simple" :label="$t('kh.simple.title')" color="primary" hide-details density="compact" />
      <div v-if="khFamily.rows.length > 1" class="d-flex justify-end">
        <v-btn variant="text" size="small" :prepend-icon="$globals.icons.delete" @click="removeRow(index)">
          {{ $t("kh.wizard.family.remove") }}
        </v-btn>
      </div>
    </v-card>

    <div class="d-flex flex-wrap ga-2 mb-4">
      <v-btn variant="tonal" :prepend-icon="$globals.icons.createAlt" @click="addRow">
        {{ $t("kh.wizard.family.more") }}
      </v-btn>
      <v-btn color="primary" :disabled="!canCreate" :loading="busy" @click="create">
        {{ $t("kh.wizard.family.create", filled.length) }}
      </v-btn>
    </div>

    <v-alert v-if="!$khFeatures.emailReady" type="info" variant="tonal" density="compact" class="mb-4">
      {{ $t("kh.wizard.family.invite-hint") }}
    </v-alert>

    <template v-if="khFamily.created.length">
      <h2 class="text-h6 mb-1">
        {{ $t("kh.wizard.family.created-title") }}
      </h2>
      <p class="text-body-2 mb-2">
        {{ $t("kh.wizard.family.created-hint") }}
      </p>
      <v-card v-for="person in khFamily.created" :key="person.username" variant="tonal" color="success" class="mb-2 pa-3">
        <div class="d-flex align-center">
          <span class="text-body-2 text-break flex-grow-1">{{ welcomeText(person) }}</span>
          <AppButtonCopy :copy-text="welcomeText(person)" />
        </div>
      </v-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { welcomeAddress } from "../lib/setup-wizard";
import { khFamily, useKhSetupFamily, type CreatedPerson } from "../composables/use-kh-setup-family";

const i18n = useI18n();
const { $globals, $khFeatures } = useNuxtApp();
const { problems, filled, canCreate, addRow, removeRow, clearFailure, create: createRows } = useKhSetupFamily();
const busy = ref(false);

// Which field shows which problem; "failed" (the call did not work) sits under the username
const FIELD_OF = { name: "name", username: "username", spaces: "username", twice: "username", taken: "username", failed: "username", email: "email" } as const;

/** What is wrong with a row in this field: its own check first, then the server's answer after trying to create it. */
function message(index: number, field: "name" | "username" | "email"): string {
  const problem = problems.value[index] ?? khFamily.failures[index];
  return problem && FIELD_OF[problem] === field ? i18n.t(`kh.wizard.family.problem.${problem}`) : "";
}

async function create() {
  busy.value = true;
  await createRows();
  busy.value = false;
}

/** The sentence for the new person, ready to send or read out. */
function welcomeText(person: CreatedPerson): string {
  return i18n.t("kh.wizard.family.welcome", {
    origin: welcomeAddress($khFeatures.baseUrl, window.location.origin), username: person.username, password: person.password, name: person.name,
  });
}
</script>
