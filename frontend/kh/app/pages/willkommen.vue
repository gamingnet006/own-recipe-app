<!-- KH: public page of the welcome mail (D53): the new person chooses a password with the link's token, then signs in. -->
<template>
  <v-container fluid class="d-flex justify-center align-center">
    <v-card color="background d-flex flex-column align-center" flat width="600px">
      <template v-if="info">
        <v-card-title class="text-h5 justify-center">
          {{ $t("kh.onboarding.welcome.title", { name: info.fullName || info.username }) }}
        </v-card-title>
        <v-card-text>
          {{ $t("kh.onboarding.welcome.hint", { username: info.username }) }}
        </v-card-text>
        <v-form class="w-100 pa-4" @submit.prevent="save">
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
      </template>
      <v-card-text v-else class="text-center">
        <p>{{ problem }}</p>
        <p>{{ $t("kh.onboarding.ask-admin") }}</p>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { failureText } from "../lib/onboarding";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { useRequests } from "~/composables/api/api-client";
import { useRouteQuery } from "~/composables/use-router";
import { validators } from "~/composables/use-validators";
import { alert } from "~/composables/use-toast";

definePageMeta({ layout: "basic" });

const i18n = useI18n();
useSeoMeta({ title: i18n.t("user.login") });

const token = useRouteQuery("token", "");
const api = new KhOnboardingApi(useRequests());
const password = ref("");
const passwordRepeat = ref("");
const busy = ref(false);
const problem = ref(i18n.t("kh.onboarding.link-invalid"));
const passwordMatch = () => password.value === passwordRepeat.value || i18n.t("user.password-must-match");

// Who the link is for; an invalid or expired link shows the message instead of the form.
const { data: info } = await api.welcomeInfo(token.value);

/** Sets the first password with the link's token, then goes to the sign-in with a success message. */
async function save() {
  if (password.value !== passwordRepeat.value) return;
  busy.value = true;
  const { error } = await api.acceptWelcome(token.value, password.value);
  busy.value = false;
  if (error) {
    alert.error(failureText(error, i18n.t("events.something-went-wrong")));
    return;
  }
  alert.success(i18n.t("kh.onboarding.welcome.saved"));
  await navigateTo("/login");
}
</script>
