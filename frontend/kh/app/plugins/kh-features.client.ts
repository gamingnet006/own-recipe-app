// KH: loads Küchenhelfer's switches once at start (GET /api/kh/features), like Mealie's app-info
// plugin; components read them as $khFeatures. Without an answer every hidden Mealie part stays hidden.
import axios from "axios";

export interface KhFeatures {
  shareLinks: boolean;
  noticePollMinutes: number; // how often the bell asks for new notices (D39)
  sourceUrl: string; // where the source of this fork can be read (AGPL), from KH_SOURCE_URL
  clockShortcutUrl: string | null; // ready-made Clock timer shortcut to add, null while not configured (D42)
  media: boolean; // own audio and video files are accepted, because a Whisper server is set (P7.3)
  profile: string; // leicht, normal, stark or lokal (P7.4)
}

const ALL_HIDDEN: KhFeatures = {
  shareLinks: false,
  noticePollMinutes: 5,
  sourceUrl: "https://github.com/gamingnet006/own-recipe-app",
  clockShortcutUrl: null,
  media: false,
  profile: "leicht",
};

export default defineNuxtPlugin({
  async setup() {
    let khFeatures = ALL_HIDDEN;
    try {
      const { data } = await axios.get<KhFeatures>("/api/kh/features");
      khFeatures = { ...ALL_HIDDEN, ...data };
    }
    catch (error) {
      console.error("Küchenhelfer: switches not loaded, hidden parts stay hidden", error);
    }

    return {
      provide: {
        khFeatures,
      },
    };
  },
});
