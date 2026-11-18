<!-- KH: first steps after the first sign-in (D53): choose an own password, give an e-mail address; then on to the start page. -->
<template>
  <v-container fluid class="d-flex justify-center align-center">
    <v-card color="background d-flex flex-column align-center" flat width="600px">
      <v-card-title class="text-h5 justify-center">
        {{ $t("kh.onboarding.first-steps") }}
      </v-card-title>
      <v-card-text class="text-center">
        {{ $t("kh.onboarding.first-steps-hint") }}
      </v-card-text>
      <BaseDivider />

      <v-form v-if="status?.mustChangePassword" class="w-100 pa-4" @submit.prevent="savePassword">
        <div class="text-h6">
          {{ $t("kh.onboarding.password.title") }}
        </div>
        <p class="mb-4">
          {{ $t("kh.onboarding.password.hint") }}
        </p>
        <v-text-field
          v-model="password"
          type="password"
          variant="solo-filled"
          flat
          autofocus
          :prepend-inner-icon="$globals.icons.lock"
          :label="$t('kh.onboarding.password.new')"
          :rules="[validators.required]"
        />
        <v-text-field
          v-model="passwordRepeat"
          type="password"
          variant="solo-filled"
          flat
          :prepend-inner-icon="$globals.icons.lock"
          :label="$t('kh.onboarding.password.repeat')"
          :rules="[validators.required, passwordMatch]"
        />
        <v-btn type="submit" color="primary" block :loading="busy">
          {{ $t("kh.onboarding.password.save") }}
        </v-btn>
      </v-form>

      <v-form v-else-if="status?.needsEmail" class="w-100 pa-4" @submit.prevent="sendEmail">
        <div class="text-h6">
          {{ $t("kh.onboarding.email.title") }}
        </div>
        <p class="mb-4">
          {{ $t("kh.onboarding.email.hint") }}
        </p>
        <v-text-field
          v-model="email"
          type="email"
          variant="solo-filled"
          flat
          autofocus
          :prepend-inner-icon="$globals.icons.email"
          :label="$t('user.email')"
          :rules="[validators.required, validators.email]"
        />
        <p v-if="status.pendingEmail" class="mb-4">
          {{ $t("kh.onboarding.email.sent", { email: status.pendingEmail }) }}
        </p>
        <v-btn type="submit" color="primary" block class="mb-2" :loading="busy">
          {{ status.pendingEmail ? $t("kh.onboarding.email.resend") : $t("kh.onboarding.email.send") }}
        </v-btn>
        <v-btn v-if="status.pendingEmail" variant="text" block @click="checkConfirmed">
          {{ $t("kh.onboarding.email.checked") }}
        </v-btn>
      </v-form>

      <v-btn class="mb-4" variant="text" @click="signOut">
        {{ $t("user.logout") }}
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { khOnboarding, useKhOnboarding } from "../composables/use-kh-onboarding";
import { validators } from "~/composables/use-validators";
import { alert } from "~/composables/use-toast";

definePageMeta({
  layout: "basic",
  middleware: ["auth"],
});

const i18n = useI18n();
const auth = useMealieAuth();
const onboarding = useKhOnboarding();
useSeoMeta({ title: i18n.t("kh.onboarding.first-steps") });

const status = computed(() => khOnboarding.status);
const password = ref("");
const passwordRepeat = ref("");
const email = ref("");
const busy = ref(false);
const passwordMatch = () => password.value === passwordRepeat.value || i18n.t("user.password-must-match");

// Fresh status on arrival; once nothing is open the person goes to the start page.
await onboarding.refresh();
// Without a status (request failed) nothing can be done here, so the person goes on instead of facing a dead end.
watch(status, (value) => {
  if (!value || (!value.mustChangePassword && !value.needsEmail)) navigateTo(`/g/${auth.user.value?.groupSlug}`);
}, { immediate: true });

/** Sets the own password (the new token is set by the composable); shows the server's message on failure. */
async function savePassword() {
  if (password.value !== passwordRepeat.value) return;
  busy.value = true;
  const failed = await onboarding.setPassword(password.value, i18n.t("events.something-went-wrong"));
  busy.value = false;
  if (failed) alert.error(failed);
  else alert.success(i18n.t("kh.onboarding.password.saved"));
}

/** Asks for the verification mail; shows the server's message (mail not set up, address taken, ...) on failure. */
async function sendEmail() {
  busy.value = true;
  const failed = await onboarding.requestEmail(email.value, i18n.t("events.something-went-wrong"));
  busy.value = false;
  if (failed) alert.error(failed);
}

/** Reads the status again after the person opened the link from the mail. */
async function checkConfirmed() {
  await onboarding.refresh();
  if (status.value?.needsEmail) alert.warning(i18n.t("kh.onboarding.email.not-yet"));
}

async function signOut() {
  onboarding.reset();
  await auth.signOut("/login?direct=1");
}
</script>
