<!-- KH: "More > About Kochheft" (P8.1): the version, what it is built on (Mealie, AGPL-3.0), where the source can be
read, and the third-party components from THIRD_PARTY_NOTICES.md. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.about.title") }}
      </template>
    </BasePageTitle>

    <v-alert v-if="failed" type="error" variant="tonal">
      {{ $t("kh.about.failed") }}
    </v-alert>
    <template v-else-if="about">
      <v-card class="mb-4">
        <v-card-text>
          <p class="text-h6">
            {{ $t("kh.about.version", { version: about.version }) }}
          </p>
          <p class="mt-2">
            {{ $t("kh.about.built-on") }}
          </p>
          <p>{{ $t("kh.about.copyright") }}</p>
          <p>{{ $t("kh.about.license") }}</p>
          <v-btn :href="$khFeatures.sourceUrl" target="_blank" rel="noopener" color="primary" class="mt-3">
            {{ $t("kh.about.source") }}
          </v-btn>
          <v-btn class="mt-3 ml-2" @click="newsOpen = true">
            {{ $t("kh.about.news") }}
          </v-btn>
        </v-card-text>
      </v-card>

      <h2 class="text-h6 mb-2">
        {{ $t("kh.about.leaves-title") }}
      </h2>
      <v-card class="mb-4">
        <v-card-text>
          <p>{{ $t("kh.about.leaves-intro") }}</p>
          <ul class="ml-6">
            <li v-for="key in LEAVES" :key="key">
              {{ $t(`kh.about.leaves.${key}`) }}
            </li>
          </ul>
          <a :href="readmeUrl" target="_blank" rel="noopener" class="d-inline-block mt-2">
            {{ $t("kh.about.leaves-details") }}
          </a>
        </v-card-text>
      </v-card>

      <h2 class="text-h6 mb-2">
        {{ $t("kh.about.notices") }}
      </h2>
      <v-card v-if="about.notices">
        <v-card-text class="kh-notices">
          <SafeMarkdown :source="about.notices" />
        </v-card-text>
      </v-card>
      <p v-else class="text-medium-emphasis">
        {{ $t("kh.about.notices-missing") }}
      </p>
    </template>
    <v-progress-linear v-else indeterminate />
    <KhNews v-model="newsOpen" :news="allNews" />
  </v-container>
</template>

<script setup lang="ts">
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { KhSystemApi, type KhAbout } from "~~/kh/app/lib/api/system";
import { forAddons, WHATS_NEW } from "~~/kh/app/lib/whats-new";
import { useRequests } from "~/composables/api/api-client";

definePageMeta({
  middleware: ["auth", "group-only"],
});

// The rows of "What leaves the house?", short forms of the README table "What goes where"
const LEAVES = ["link", "ai", "push", "tunnel", "updates"];

const i18n = useI18n();
const auth = useMealieAuth();
const { $khFeatures } = useNuxtApp();
const readmeUrl = `${$khFeatures.sourceUrl}/blob/main/docs/kh/README.md#${i18n.t("kh.about.readme-anchor")}`;
const newsOpen = ref(false);
const allNews = computed(() => forAddons(WHATS_NEW, khAddons.enabled, !!auth.user.value?.admin));
useSeoMeta({ title: i18n.t("kh.about.title") });

const about = ref<KhAbout | null>(null);
const failed = ref(false);

onMounted(async () => {
  const { data } = await new KhSystemApi(useRequests()).about();
  about.value = data;
  failed.value = !data;
});
</script>

<style scoped>
/* The shipped file holds wide tables; they scroll instead of widening the page */
.kh-notices {
  overflow-x: auto;
}
</style>
