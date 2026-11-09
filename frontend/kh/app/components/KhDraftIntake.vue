<!-- KH: the form of the intake (phase 2, on the drafts page since D38): a link, a text or photos become a draft,
which is recognized in the background and then waits in the list below for a review. -->
<template>
  <section>
    <h2 class="text-h6 mb-3">
      {{ $t("kh.drafts.add-recipe") }}
    </h2>
    <!-- D39: when no AI provider is set up or free, photos and texts would fail; links with recipe data still work -->
    <v-alert v-if="aiHint" type="info" variant="tonal" density="compact" class="mb-3">
      {{ $t(aiHint) }}
    </v-alert>
    <v-row dense>
      <v-col v-for="option in sources" :key="option.source" :cols="12 / sources.length">
        <v-btn
          block
          height="72"
          :color="source === option.source ? 'primary' : 'kh-hint'"
          stacked
          variant="flat"
          :prepend-icon="option.icon"
          @click="choose(option.source)"
        >
          {{ $t(`kh.drafts.source.${option.source}`) }}
        </v-btn>
      </v-col>
    </v-row>

    <v-form v-if="source" class="mt-4" @submit.prevent="submit">
      <v-text-field
        v-if="source === 'link'"
        v-model="link"
        type="url"
        autofocus
        :label="$t('kh.drafts.link-label')"
        :rules="[validators.url]"
      />
      <!-- D5: a video link is not fetched; its description or a screenshot makes the draft, the link stays the source -->
      <v-alert v-if="videoLink" type="info" variant="tonal" density="compact" class="mb-3">
        {{ $t("kh.drafts.error.video_link") }}
      </v-alert>
      <v-textarea
        v-if="source === 'text' || videoLink"
        v-model="text"
        auto-grow
        autofocus
        rows="6"
        :label="$t('kh.drafts.text-label')"
      />
      <div v-if="source === 'image' || videoLink">
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
      <!-- P7.3: an own recording, only while a Whisper server is set -->
      <div v-if="source === 'media'">
        <div v-if="recording" class="mb-3">
          {{ recording.name }}
        </div>
        <v-btn variant="tonal" :prepend-icon="$globals.icons.createAlt" @click="mediaPicker?.click()">
          {{ $t("kh.drafts.choose-media") }}
        </v-btn>
      </div>
      <v-btn type="submit" color="success" class="mt-4" :loading="sending" :disabled="!complete">
        {{ $t("general.submit") }}
      </v-btn>
    </v-form>
    <input
      ref="mediaPicker"
      type="file"
      accept="audio/*,video/*"
      hidden
      @change="chooseRecording"
    >
    <!-- No capture attribute: iOS then offers the camera and the photo library -->
    <input
      ref="picker"
      type="file"
      accept="image/*"
      multiple
      hidden
      @change="addPhotos"
    >
  </section>
</template>

<script setup lang="ts">
import type { KhDraftSource } from "~~/kh/app/lib/api/drafts";
import { errorText, isVideoLink, requestError, useKhDraftsApi } from "~~/kh/app/composables/use-kh-drafts";
import { aiHintKey, useKhAiApi } from "~~/kh/app/composables/use-kh-ai";
import { khAddons } from "~~/kh/app/composables/use-kh-addons";
import { alert } from "~/composables/use-toast";
import { validators } from "~/composables/use-validators";

// A link shared to the app arrives through Mealie's import page, which leads to the intake with it
const props = defineProps<{ sharedLink: string }>();
const emit = defineEmits<{ submitted: [] }>();

const i18n = useI18n();
const { $globals, $khFeatures } = useNuxtApp();
const api = useKhDraftsApi();

// The hint when no AI provider is set up or free right now (D39), asked once when the intake opens
const aiHint = ref<string | null>(null);
onMounted(async () => {
  const { data } = await useKhAiApi().status();
  aiHint.value = aiHintKey(data);
});

// "media" is only an option of the form: the draft it makes is a text draft (P7.3)
type IntakeSource = KhDraftSource | "media";
const sources: { source: IntakeSource; icon: string }[] = [
  { source: "link", icon: $globals.icons.link },
  { source: "text", icon: $globals.icons.textBox },
  { source: "image", icon: $globals.icons.fileImage },
  ...($khFeatures.media && khAddons.enabled.whisper ? [{ source: "media" as const, icon: $globals.icons.microphone }] : []),
];

const source = ref<IntakeSource | null>(props.sharedLink ? "link" : null);
const link = ref(props.sharedLink);
const text = ref("");
// The chosen photos with a preview address each, given back to the browser when a photo goes or the page is left
const photos = ref<{ file: File; url: string }[]>([]);
const picker = ref<HTMLInputElement | null>(null);
const mediaPicker = ref<HTMLInputElement | null>(null);
const recording = ref<File | null>(null);
const sending = ref(false);

// A video link asks for text or photos too (D5)
const videoLink = computed(() => source.value === "link" && isVideoLink(link.value));

const complete = computed(() => {
  if (videoLink.value) return text.value.trim() !== "" || photos.value.length > 0;
  if (source.value === "link") return validators.url(link.value) === true;
  if (source.value === "text") return text.value.trim() !== "";
  if (source.value === "media") return recording.value !== null;
  return photos.value.length > 0;
});

/** Picks what to hand in; photos open the camera or photo library right away. */
function choose(kind: IntakeSource) {
  source.value = kind;
  if (kind === "image" && !photos.value.length) picker.value?.click();
  if (kind === "media" && !recording.value) mediaPicker.value?.click();
}

/** Takes the one chosen recording. */
function chooseRecording(event: Event) {
  const input = event.target as HTMLInputElement;
  recording.value = input.files?.[0] ?? null;
  input.value = "";
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

/** Empties the form for the next recipe and gives the previews back to the browser. */
function clear() {
  photos.value.forEach(photo => URL.revokeObjectURL(photo.url));
  photos.value = [];
  link.value = "";
  text.value = "";
  recording.value = null;
  source.value = null;
}

onBeforeUnmount(() => photos.value.forEach(photo => URL.revokeObjectURL(photo.url)));

/** Hands in the chosen source only; the list below then shows the new draft while it is recognized. */
async function submit() {
  const form = new FormData();
  if (source.value === "link") form.append("url", link.value.trim());
  if (source.value === "text" || (videoLink.value && text.value.trim())) form.append("text", text.value.trim());
  if (source.value === "media" && recording.value) form.append("media", recording.value);
  if (source.value === "image" || videoLink.value) photos.value.forEach(photo => form.append("images", photo.file));

  sending.value = true;
  const { error } = await api.create(form);
  sending.value = false;
  if (error) {
    alert.error(errorText(requestError(error).code, i18n.t));
    return;
  }
  clear();
  emit("submitted");
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
