<!-- KH: the drafts intake (phase 2): a link, a text or photos become a draft, which is recognized in the
background and then waits in the drafts list for a review. -->
<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #title>
        {{ $t("kh.drafts.add-recipe") }}
      </template>
      {{ $t("kh.drafts.intake-description") }}
    </BasePageTitle>

    <v-row dense>
      <v-col v-for="option in sources" :key="option.source" cols="12" sm="4">
        <v-btn
          block
          height="88"
          color="primary"
          :variant="source === option.source ? 'flat' : 'tonal'"
          :prepend-icon="option.icon"
          @click="choose(option.source)"
        >
          {{ $t(`kh.drafts.source.${option.source}`) }}
        </v-btn>
      </v-col>
    </v-row>

    <v-form v-if="source" class="mt-6" @submit.prevent="submit">
      <v-text-field
        v-if="source === 'link'"
        v-model="link"
        type="url"
        autofocus
        :label="$t('kh.drafts.link-label')"
        :rules="[validators.url]"
      />
      <v-textarea
        v-else-if="source === 'text'"
        v-model="text"
        auto-grow
        autofocus
        rows="6"
        :label="$t('kh.drafts.text-label')"
      />
      <div v-else>
        <div v-if="photos.length" class="d-flex flex-wrap ga-2 mb-3">
          <div v-for="(photo, index) in photos" :key="photo.url" class="kh-photo">
            <v-img :src="photo.url" width="88" height="88" cover rounded />
            <v-btn
              icon
              size="x-small"
              class="kh-photo-remove"
              :aria-label="$t('kh.drafts.remove-photo')"
              @click="removePhoto(index)"
            >
              <v-icon :icon="$globals.icons.close" />
            </v-btn>
          </div>
        </div>
        <v-btn variant="tonal" :prepend-icon="$globals.icons.createAlt" @click="picker?.click()">
          {{ $t("kh.drafts.add-photos") }}
        </v-btn>
      </div>
      <v-btn type="submit" color="success" class="mt-4" :loading="sending" :disabled="!complete">
        {{ $t("general.submit") }}
      </v-btn>
    </v-form>
    <!-- No capture attribute: iOS then offers the camera and the photo library -->
    <input
      ref="picker"
      type="file"
      accept="image/*"
      multiple
      hidden
      @change="addPhotos"
    >
  </v-container>
</template>

<script setup lang="ts">
import type { KhDraftSource } from "~~/kh/app/lib/api/drafts";
import { errorText, requestError, useKhDraftsApi } from "~~/kh/app/composables/use-kh-drafts";
import { alert } from "~/composables/use-toast";
import { validators } from "~/composables/use-validators";

definePageMeta({
  middleware: ["auth", "group-only"],
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const route = useRoute();
const router = useRouter();
const api = useKhDraftsApi();

useSeoMeta({ title: i18n.t("kh.drafts.add-recipe") });

const sources = [
  { source: "link", icon: $globals.icons.link },
  { source: "text", icon: $globals.icons.textBox },
  { source: "image", icon: $globals.icons.fileImage },
] as const;

// A link shared to the app arrives through Mealie's import page, which leads here with this query
const sharedLink = typeof route.query.recipe_import_url === "string" ? route.query.recipe_import_url : "";
const source = ref<KhDraftSource | null>(sharedLink ? "link" : null);
const link = ref(sharedLink);
const text = ref("");
// The chosen photos with a preview address each, given back to the browser when a photo goes or the page is left
const photos = ref<{ file: File; url: string }[]>([]);
const picker = ref<HTMLInputElement | null>(null);
const sending = ref(false);

const complete = computed(() => {
  if (source.value === "link") return validators.url(link.value) === true;
  if (source.value === "text") return text.value.trim() !== "";
  return photos.value.length > 0;
});

/** Picks what to hand in; photos open the camera or photo library right away. */
function choose(kind: KhDraftSource) {
  source.value = kind;
  if (kind === "image" && !photos.value.length) picker.value?.click();
}

/** Collects the chosen photos, so a recipe on several pages can be photographed one page at a time. */
function addPhotos(event: Event) {
  const input = event.target as HTMLInputElement;
  const added = Array.from(input.files ?? []).map(file => ({ file, url: URL.createObjectURL(file) }));
  photos.value = [...photos.value, ...added];
  input.value = ""; // so the same photo can be chosen again
}

/** Takes a photo out again, e.g. a blurry one or one too many. */
function removePhoto(index: number) {
  URL.revokeObjectURL(photos.value[index]!.url);
  photos.value = photos.value.filter((_, i) => i !== index);
}

onBeforeUnmount(() => photos.value.forEach(photo => URL.revokeObjectURL(photo.url)));

/** Hands in the chosen source only and opens the drafts list, where the recognition can be followed. */
async function submit() {
  const form = new FormData();
  if (source.value === "link") form.append("url", link.value.trim());
  else if (source.value === "text") form.append("text", text.value.trim());
  else photos.value.forEach(photo => form.append("images", photo.file));

  sending.value = true;
  const { error } = await api.create(form);
  sending.value = false;
  if (error) {
    alert.error(errorText(requestError(error).code, i18n.t));
    return;
  }
  router.push(`/g/${route.params.groupSlug}/drafts`);
}
</script>

<style scoped>
.kh-photo {
  position: relative;
}

.kh-photo-remove {
  position: absolute;
  top: 4px;
  right: 4px;
}
</style>
