// KH: loads Küchenhelfer's switches once at start (GET /api/kh/features), like Mealie's app-info
// plugin; components read them as $khFeatures. Without an answer every hidden Mealie part stays hidden.
import axios from "axios";

export interface KhFeatures {
  shareLinks: boolean;
  noticePollMinutes: number; // how often the bell asks for new notices (D39)
  clockShortcutUrl: string | null; // ready-made Clock timer shortcut to add, null while not configured (D42)
}

const ALL_HIDDEN: KhFeatures = { shareLinks: false, noticePollMinutes: 5, clockShortcutUrl: null };

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
