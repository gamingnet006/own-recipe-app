// KH: loads Kochheft's switches once at start (GET /api/kh/features), like Mealie's app-info
// plugin; components read them as $khFeatures. Without an answer every hidden Mealie part stays hidden.
import axios from "axios";

export interface KhFeatures {
  shareLinks: boolean;
  noticePollMinutes: number; // how often the bell asks for new notices (D39)
  sourceUrl: string; // where the source of this fork can be read (AGPL), from KH_SOURCE_URL
  clockShortcutUrl: string | null; // ready-made Clock timer shortcut to add, null while not configured (D42)
  importShortcutUrl: string | null; // ready-made share-sheet import shortcut, null while not configured (D68)
  siriShortcutUrl: string | null; // ready-made "Auf die Einkaufsliste" Siri shortcut, null while not configured (D68)
  media: boolean; // own audio and video files are accepted, because a Whisper server is set (P7.3)
  profile: string; // leicht, normal, stark or lokal (P7.4)
  emailReady: boolean; // mail sending is set up, so reset links and verification mails work (D53)
  draftMaxText: number; // longest recipe text one draft takes; a text shared into the app is cut here (D57)
}

// A slow server must not hold the whole app start: without an answer the hidden parts stay hidden.
const FEATURES_TIMEOUT_MS = 5000;

const ALL_HIDDEN: KhFeatures = {
  shareLinks: false,
  noticePollMinutes: 5,
  sourceUrl: "https://github.com/gamingnet006/own-recipe-app",
  clockShortcutUrl: null,
  importShortcutUrl: null,
  siriShortcutUrl: null,
  media: false,
  profile: "leicht",
  emailReady: false,
  draftMaxText: 20000,
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
