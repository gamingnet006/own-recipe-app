// KH: finds durations ("10 Min.", "20–30 Minuten", "eine halbe Stunde") in a step text so they can become
// timers (D42, cook mode). Pure function, German and English units.

/** A duration found in a text; START/END cut it from the text, UPPERSECONDS is the end of a range. */
export interface KhTime {
  start: number;
  end: number;
  text: string;
  seconds: number;
  upperSeconds: number | null;
}

const NUMBER_WORDS: Record<string, number> = {
  ein: 1, eine: 1, einer: 1, zwei: 2, drei: 3, vier: 4, fünf: 5, sechs: 6, sieben: 7, acht: 8, neun: 9, zehn: 10, elf: 11, zwölf: 12,
};
const FRACTIONS: Record<string, number> = { "½": 0.5, "¼": 0.25, "¾": 0.75 };
// Fixed phrases whose duration needs no number.
const PHRASES: Record<string, number> = { "halbe stunde": 1800, "viertelstunde": 900, "dreiviertelstunde": 2700, "anderthalb stunden": 5400 };

const SECOND_UNIT = "Sekunden?|Sek\\.?|seconds?|secs?";
const MINUTE_UNIT = "Minuten?|Min\\.?|minutes?|mins?";
const HOUR_UNIT = "Stunden?|Std\\.?|hours?|hrs?";
const NOT_WORD = "(?![\\p{L}\\d])";
const unit = (alternatives: string) => `(?:${alternatives})${NOT_WORD}`;
const AMOUNT = `(?:\\d+\\s+\\d+/[1-9]\\d*|\\d+/[1-9]\\d*|\\d+(?:[.,]\\d+)?(?:\\s?[½¼¾])?|[½¼¾]|(?:${Object.keys(NUMBER_WORDS).join("|")})${NOT_WORD})`;
const RANGE_SEPARATOR = "(?:\\s*[-–]\\s*|\\s+bis\\s+)";
const START = "(?<![\\p{L}\\d/])"; // not inside "1/2", which would read as 2
const flags = "giu";

// "1 Std. 20 Min." as one timer; hours group first, minutes second.
const COMBINATION = new RegExp(`${START}(${AMOUNT})\\s*${unit(HOUR_UNIT)}\\s+(?:und\\s+)?(${AMOUNT})\\s*${unit(MINUTE_UNIT)}`, flags);
// "10 Min.", "20–30 Minuten": amount, optional range end, unit.
const SINGLE = new RegExp(`${START}(${AMOUNT})(?:${RANGE_SEPARATOR}(${AMOUNT}))?\\s*(${unit(`${SECOND_UNIT}|${MINUTE_UNIT}|${HOUR_UNIT}`)})`, flags);
const PHRASE = new RegExp(`${START}(?:eine?\\s+)?(${Object.keys(PHRASES).join("|").replace(/ /g, "\\s+")})${NOT_WORD}`, flags);

/** The number a matched amount stands for ("1,5", "1½", "1 ½", "1/2", "1 1/2", "zwölf"). */
function amountValue(amount: string): number {
  const word = NUMBER_WORDS[amount.toLowerCase()];
  if (word !== undefined) return word;
  const written = amount.match(/^(?:(\d+)\s+)?(\d+)\/(\d+)$/);
  if (written) return Number(written[1] ?? 0) + Number(written[2]) / Number(written[3]);
  const [, digits = "0", fraction] = amount.match(/^(\d+(?:[.,]\d+)?)?\s?([½¼¾])?$/) ?? [];
  return Number(digits.replace(",", ".")) + (fraction ? FRACTIONS[fraction]! : 0);
}

/** Seconds in one of the units above, told apart by its first letters. */
function unitSeconds(name: string): number {
  if (/^(sek|sec)/i.test(name)) return 1;
  return /^min/i.test(name) ? 60 : 3600;
}

/** Every duration with a fixed length in TEXT, in order of appearance; ranges give both ends. Phrases like
 * "über Nacht" or "einige Stunden" are left alone. */
export function parseTimes(text: string): KhTime[] {
  const found: KhTime[] = [];
  const add = (m: RegExpMatchArray, seconds: number, upperSeconds: number | null = null) =>
    found.push({ start: m.index!, end: m.index! + m[0].length, text: m[0], seconds, upperSeconds });

  for (const m of text.matchAll(COMBINATION)) add(m, amountValue(m[1]!) * 3600 + amountValue(m[2]!) * 60);
  for (const m of text.matchAll(PHRASE)) add(m, PHRASES[m[1]!.toLowerCase().replace(/\s+/g, " ")]!);
  for (const m of text.matchAll(SINGLE)) {
    const factor = unitSeconds(m[3]!);
    const upper = m[2] ? amountValue(m[2]) * factor : null;
    const seconds = amountValue(m[1]!) * factor;
    // A reversed range ("30–20 Min.") is nonsense at its upper end; only the first number counts.
    add(m, seconds, upper !== null && upper > seconds ? upper : null);
  }

  // Longest match first at the same start, then drop whatever overlaps an earlier keeper (the single "1 Std." inside "1 Std. 20 Min.").
  found.sort((a, b) => a.start - b.start || b.end - a.end);
  const kept: KhTime[] = [];
  for (const time of found) {
    if (!kept.length || time.start >= kept[kept.length - 1]!.end) kept.push(time);
  }
  return kept;
}
