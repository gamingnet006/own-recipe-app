// KH: loads Kochheft's switches once at start (GET /api/kh/features), like Mealie's app-info
// plugin; components read them as $khFeatures. Without an answer every hidden Mealie part stays hidden.
import axios from "axios";
import type { KhShortcutUrls } from "../lib/device-setup";

export interface KhFeatures {
  shareLinks: boolean;
  noticePollMinutes: number; // how often the bell asks for new notices (D39)
  sourceUrl: string; // where the source of this fork can be read (AGPL), from KH_SOURCE_URL
  shortcutUrls: Record<string, KhShortcutUrls>; // ready-made shortcuts to add per language ("de-DE", "en-US"), see shortcutUrlsFor
  media: boolean; // own audio and video files are accepted, because a Whisper server is set (P7.3)
  profile: string; // leicht, normal, stark or lokal (P7.4)
  emailReady: boolean; // mail sending is set up, so reset links and verification mails work (D53)
  draftMaxText: number; // longest recipe text one draft takes; a text shared into the app is cut here (D57)
  baseUrl: string | null; // Mealie's BASE_URL, null while it is still the default (D83)
  addressChangedAt: string | null; // when the address last changed, null after 60 days or if never (D85)
}

// A slow server must not hold the whole app start: without an answer the hidden parts stay hidden.
const FEATURES_TIMEOUT_MS = 5000;

const ALL_HIDDEN: KhFeatures = {
  shareLinks: false,
  noticePollMinutes: 5,
  sourceUrl: "https://github.com/gamingnet006/own-recipe-app",
  shortcutUrls: {},
  media: false,
  profile: "leicht",
  emailReady: false,
  draftMaxText: 20000,
  baseUrl: null,
  addressChangedAt: null,
};

export default defineNuxtPlugin({
  async setup() {
    let khFeatures = ALL_HIDDEN;
    try {
      const { data } = await axios.get<KhFeatures>("/api/kh/features", { timeout: FEATURES_TIMEOUT_MS });
      khFeatures = { ...ALL_HIDDEN, ...data };
    }
    catch (error) {
      console.error("Kochheft: switches not loaded, hidden parts stay hidden", error);
    }

    return {
      provide: {
        khFeatures,
      },
    };
  },
});
