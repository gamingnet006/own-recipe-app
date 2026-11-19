// KH: "Teilen" in the shopping list menu (D56): the open items go to the system share sheet, or onto the clipboard
// where the browser has none.
import { useClipboard } from "@vueuse/core";
import { shareText } from "../lib/shopping-share";
import { alert } from "~/composables/use-toast";

/** Shares the list's open items; a person who cancels the share sheet sees nothing, any other failure copies. */
export function useKhShareList() {
  const { copy, copied, isSupported } = useClipboard({ legacy: true });
  const i18n = useI18n();

  /** Puts the text on the clipboard and says so; the way out where the browser has no share sheet or it failed. */
  async function copyInstead(text: string) {
    if (!isSupported.value) return alert.error(i18n.t("general.your-browser-does-not-support-clipboard"));
    await copy(text);
    if (copied.value) alert.success(i18n.t("kh.share.copied"));
    else alert.error(i18n.t("general.clipboard-copy-failure"));
  }

  async function shareList(name: string, items: Parameters<typeof shareText>[0]) {
    const text = shareText(items);
    if (!text) return alert.info(i18n.t("kh.share.empty"));
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: name, text });
        return;
      }
      catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return; // cancelled on purpose
      }
    }
    await copyInstead(text);
  }

  return { shareList };
}
