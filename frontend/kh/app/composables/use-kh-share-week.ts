// KH: "Woche teilen" in the meal planner (D73): the shown days as text to the share sheet, or onto the clipboard where
// there is none. Sharing and copying are the ones of the recipe text export (D61).
import { shareText, copyText } from "./use-kh-recipe-text";
import { weekText, type WeekTextDay } from "../lib/week-text";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

/** Shares the planned entries of DAYS; says so when nothing is planned. */
export async function shareWeek(days: WeekTextDay[]): Promise<void> {
  const i18n = useGlobalI18n();
  const title = i18n.t("kh.week-share.title");
  const text = weekText(days, title, window.location.origin, i18n.locale.value);
  if (!text) return alert.info(i18n.t("kh.week-share.empty"));
  if (await shareText(title, text)) return;
  if (await copyText(text)) alert.success(i18n.t("kh.share.copied"));
  else alert.error(i18n.t("general.clipboard-copy-failure"));
}
