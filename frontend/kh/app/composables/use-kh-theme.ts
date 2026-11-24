// KH: the look choice System / Hell / Dunkel, per device. It keeps vueuse's stored value ("auto", "light", "dark"
// under "vueuse-color-scheme"), so choices made with Mealie's old toggle carry over, and sets the page's "dark" class.
import { computed } from "vue";
import { useColorMode } from "@vueuse/core";
import { parseThemeChoice, resolveTheme, type ThemeChoice } from "../lib/theme";

/** The person's choice (writable) and the look it gives right now; "System" follows the device live. */
export function useKhTheme() {
  const mode = useColorMode({ emitAuto: true, modes: { light: "", dark: "dark" } }); // as useDark's classes
  const choice = computed<ThemeChoice>({
    get: () => parseThemeChoice(mode.store.value),
    set: (value) => {
      mode.store.value = value;
    },
  });
  const resolved = computed(() => resolveTheme(choice.value, mode.system.value === "dark"));
  return { choice, resolved };
}
