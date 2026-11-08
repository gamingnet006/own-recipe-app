// KH: the cook-mode timers (D42): one shared list per page, kept in localStorage, each timer remembering its end
// time (not the seconds left) so sleep and locked screens cannot make it late; plus the alarm and the clock link.
import { computed, ref, watch } from "vue";
import type { KhTime } from "../lib/times";
import { uuid4 } from "~/composables/use-utils";

const STORAGE_KEY = "kh-timers";
/** The alarm stops by itself after this long if nobody taps "Aus". */
export const ALARM_MAX_MS = 120_000;
const ALARM_ROUND_MS = 1000;
const BEEP_HZ = 880;
const BEEP_SECONDS = 0.3;
const VIBRATION_PATTERN = [300, 200, 300];
// How often the ringing list looks at the clock again.
const TICK_MS = 1000;

export interface KhTimer {
  id: string;
  label: string;
  recipeSlug: string;
  /** Epoch milliseconds when it rings; meaningless while paused. */
  endsAt: number;
  seconds: number;
  /** Seconds to add for a range timer when it rings at the lower end; null if there is no more. */
  extraSeconds: number | null;
  /** Milliseconds left while paused, else null. */
  pausedLeft: number | null;
}

/** The stored list; broken or foreign data counts as no timers. */
function loadTimers(): KhTimer[] {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(stored) ? stored : [];
  }
  catch {
    return [];
  }
}

// The app runs without server rendering, so module state is shared by all users of the timers.
const timers = ref<KhTimer[]>(loadTimers());
const tick = ref(0);
let ticker: ReturnType<typeof setInterval> | undefined;
watch(timers, list => localStorage.setItem(STORAGE_KEY, JSON.stringify(list)), { deep: true, flush: "sync" });

/** The shared timers; NOW is the clock, replaceable for tests. `tick` changes every second: read it in a render
 * to show `left` afresh. */
export function useKhTimers(now: () => number = Date.now) {
  // Starts once, so `ringing` notices a timer running out without anybody touching it.
  ticker ??= setInterval(() => tick.value++, TICK_MS);

  const find = (id: string) => timers.value.find(t => t.id === id);

  /** Whole seconds left, rounded up; 0 when done. */
  function left(timer: KhTimer): number {
    const ms = timer.pausedLeft ?? timer.endsAt - now();
    return Math.max(0, Math.ceil(ms / 1000));
  }

  /** Whether the timer has run out (a paused one has not). */
  function done(timer: KhTimer): boolean {
    return timer.pausedLeft === null && timer.endsAt <= now();
  }

  /** Starts a timer for TIME, named LABEL, belonging to the recipe RECIPESLUG. */
  function start(time: KhTime, label: string, recipeSlug: string): KhTimer {
    const extraSeconds = time.upperSeconds === null ? null : time.upperSeconds - time.seconds;
    timers.value.push({ id: uuid4(), label, recipeSlug, endsAt: now() + time.seconds * 1000, seconds: time.seconds, extraSeconds, pausedLeft: null });
    return timers.value[timers.value.length - 1]!;
  }

  /** Holds a running timer; the time left stays. */
  function pause(id: string): void {
    const timer = find(id);
    if (timer && timer.pausedLeft === null) timer.pausedLeft = Math.max(0, timer.endsAt - now());
  }

  /** Lets a paused timer run on with the time it had left. */
  function resume(id: string): void {
    const timer = find(id);
    if (timer?.pausedLeft == null) return;
    timer.endsAt = now() + timer.pausedLeft;
    timer.pausedLeft = null;
  }

  /** Removes a timer. */
  function stop(id: string): void {
    timers.value = timers.value.filter(t => t.id !== id);
  }

  /** Restarts a range timer that rang at the lower end for the rest up to the upper end. */
  function extend(id: string): void {
    const timer = find(id);
    if (!timer?.extraSeconds) return;
    timer.endsAt = now() + timer.extraSeconds * 1000;
    timer.seconds = timer.extraSeconds;
    timer.extraSeconds = null;
  }

  const ringing = computed(() => {
    void tick.value;
    return timers.value.filter(done);
  });

  return { timers, start, pause, resume, stop, extend, left, done, ringing, tick };
}

let audio: AudioContext | undefined;

/** Allows sounds: iOS only plays Web Audio that was started by a tap, so call this from the first timer tap. */
export function unlockAudio(): void {
  audio ??= new AudioContext();
  void audio.resume();
}

/** One short beep, if sound was unlocked. */
function beep(): void {
  if (!audio) return;
  const oscillator = audio.createOscillator();
  oscillator.frequency.value = BEEP_HZ;
  oscillator.connect(audio.destination);
  oscillator.start();
  oscillator.stop(audio.currentTime + BEEP_SECONDS);
}

/** Beeps and vibrates once per round until the returned function is called or ALARM_MAX_MS is over. */
export function startAlarm(): () => void {
  const round = () => {
    beep();
    navigator.vibrate?.(VIBRATION_PATTERN);
  };
  round();
  const rounds = setInterval(round, ALARM_ROUND_MS);
  const limit = setTimeout(() => clearInterval(rounds), ALARM_MAX_MS);
  return () => {
    clearInterval(rounds);
    clearTimeout(limit);
  };
}

/** The address that starts an iOS Shortcut named NAME with the minutes (rounded up) for the clock app's timer. */
export function clockTimerUrl(name: string, seconds: number): string {
  return `shortcuts://run-shortcut?name=${encodeURIComponent(name)}&input=text&text=${Math.ceil(seconds / 60)}`;
}
