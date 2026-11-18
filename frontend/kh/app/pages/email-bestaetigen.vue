<!-- KH: public page of the verification mail (D53): confirms the address with the link's token on load. -->
<template>
  <v-container fluid class="d-flex justify-center align-center">
    <v-card color="background d-flex flex-column align-center" flat width="600px">
      <v-card-title class="text-h5 justify-center">
        {{ $t("kh.onboarding.confirm.title") }}
      </v-card-title>
      <v-card-text class="text-center">
        {{ message }}
      </v-card-text>
      <v-btn class="mb-4" color="primary" to="/login">
        {{ $t("user.login") }}
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { failureText } from "../lib/onboarding";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { useKhOnboarding } from "../composables/use-kh-onboarding";
import { useRequests } from "~/composables/api/api-client";
import { useRouteQuery } from "~/composables/use-router";

definePageMeta({ layout: "basic" });

const i18n = useI18n();
useSeoMeta({ title: i18n.t("kh.onboarding.confirm.title") });

const token = useRouteQuery("token", "");
const { error } = await new KhOnboardingApi(useRequests()).confirmEmail(token.value);
// The cached first-steps status is stale now; the next page load reads it again.
useKhOnboarding().reset();
const message = error ? failureText(error, i18n.t("kh.onboarding.link-invalid")) : i18n.t("kh.onboarding.confirm.done");
</script>
