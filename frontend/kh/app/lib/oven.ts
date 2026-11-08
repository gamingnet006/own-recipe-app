// KH: the fan-oven bracket (D43, F6): finds oven temperatures in a step text and says what they are in the
// reader's own oven type ("180 °C" -> "(Umluft 160 °C)"). Pure functions plus the per-device setting.
import { ref, watch } from "vue";

export type Oven = "conventional" | "fan";

/** Degrees Celsius a fan oven runs cooler than a conventional one for the same result. */
export const OVEN_FAN_DIFFERENCE = 20;
/** Below this a temperature is rarely an oven's ("auf 60 °C abkühlen"), so it gets no bracket. */
export const OVEN_MIN_TEMPERATURE = 100;
/** How many words around a temperature may state its oven type. */
const OVEN_TYPE_WORDS = 3;
const STORAGE_KEY = "kh-oven";

// The bracket shows the labels of the recipe's own language (German, like the words that are searched for).
const LABELS: Record<Oven, string> = { conventional: "Ober-/Unterhitze", fan: "Umluft" };

// "180 °C", "180°C", "180 Grad", ranges "180-200 °C"; the lookbehind rules out decimals, longer numbers and minus signs.
const TEMPERATURE = /(?<![\p{L}\d.,−])(\d{2,3})(?:\s*[-–]\s*(\d{2,3}))?\s*(?:°\s?C|Grad)(?![\p{L}\d])/giu;
// Words naming the oven type: group 1 is the fan, anything else matched is conventional.
const OVEN_TYPE = /(umluft)|ober-?\s*(?:[/&]|und)\s*unterhitze|(?<![\p{L}\d])o\/u(?![\p{L}\d])/giu;
const WORD = /[^\s,;:.()]+/g;
// "um 180 Grad drehen": an angle for turning the tray, not an oven temperature (before: "um"; after: a turning verb
// within two words).
const TURN_BEFORE = /(?<![\p{L}\d])um\s+$/iu;
const TURN_AFTER = /^\s*(?:[^\s,;:.()]+\s+){0,2}(?:dreh|wend|gedreht|gewendet)/iu;

/** The oven type stated by the words around the temperature at START..END of TEXT (within LOW..HIGH, the room
 * left by the neighbouring temperatures); the nearest statement wins. Null if the text states none. */
function statedOven(text: string, start: number, end: number, low: number, high: number): Oven | null {
  const before = [...text.slice(low, start).matchAll(WORD)].slice(-OVEN_TYPE_WORDS);
  const after = [...text.slice(end, high).matchAll(WORD)].slice(0, OVEN_TYPE_WORDS);
  const from = before.length ? low + before[0]!.index : start;
  const last = after.at(-1);
  const to = last ? end + last.index + last[0].length : end;
  let nearest: { distance: number; oven: Oven } | null = null;
  for (const m of text.slice(from, to).matchAll(OVEN_TYPE)) {
    const at = from + m.index;
    const distance = at < start ? start - (at + m[0].length) : at - end;
    if (!nearest || distance < nearest.distance) nearest = { distance, oven: m[1] ? "fan" : "conventional" };
  }
  return nearest?.oven ?? null;
}

/** The bracket text for the temperatures LOWER (to UPPER) read in the OVEN of the reader; null if none is needed.
 * STATED is the oven type the text names. */
function bracketText(lower: number, upper: number | null, stated: Oven | null, oven: Oven): string | null {
  if (lower < OVEN_MIN_TEMPERATURE || stated === oven) return null;
  if (oven === "conventional" && stated === null) return null; // a bare temperature is read as conventional
  const shift = oven === "fan" ? -OVEN_FAN_DIFFERENCE : OVEN_FAN_DIFFERENCE;
  const value = upper === null ? `${lower + shift}` : `${lower + shift}–${upper + shift}`;
  return ` (${LABELS[oven]} ${value} °C)`;
}

/** The brackets to insert into TEXT for a reader with OVEN: AT is the offset right after each matching
 * temperature, TEXT what to insert there (with a leading space). */
export function ovenBrackets(text: string, oven: Oven): { at: number; text: string }[] {
  const found = [...text.matchAll(TEMPERATURE)];
  return found.flatMap((m, i) => {
    const end = m.index + m[0].length;
    if (TURN_BEFORE.test(text.slice(0, m.index)) || TURN_AFTER.test(text.slice(end))) return [];
    const stated = statedOven(text, m.index, end, i ? found[i - 1]!.index + found[i - 1]![0].length : 0, found[i + 1]?.index ?? text.length);
    const bracket = bracketText(Number(m[1]), m[2] ? Number(m[2]) : null, stated, oven);
    return bracket ? [{ at: end, text: bracket }] : [];
  });
}

/** The stored oven type; anything missing or broken is replaced by the standard. */
function loadOven(): Oven {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "fan" ? "fan" : "conventional";
  }
  catch {
    return "conventional";
  }
}

// The app runs without server rendering, so module state is shared by all users of the setting.
const oven = ref<Oven>(loadOven());
watch(oven, value => localStorage.setItem(STORAGE_KEY, value), { flush: "sync" });

/** The oven type of this device ("Unser Ofen"), kept on the device. */
export function useKhOven() {
  return oven;
}
