// KH: the cook-mode timers (D42): one shared list per page, kept in localStorage, each timer remembering its end
// time (not the seconds left) so sleep and locked screens cannot make it late; plus the alarm and the clock link.
import { computed, effectScope, ref, toRef, watch, type EffectScope } from "vue";
import type { KhTime } from "../lib/times";
import { uuid4 } from "~/composables/use-utils";

const STORAGE_KEY = "kh-timers";
const CLOCK_KEY = "kh-clock-timer";
/** The name of the iOS Shortcut that starts the clock app's timer, unless the device is set to another. */
export const DEFAULT_CLOCK_SHORTCUT = "Kochheft Timer";
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
  /** The 0-based step the timer was started in, so its link leads back there. */
  step: number;
  /** Epoch milliseconds when it rings; meaningless while paused. */
  endsAt: number;
  seconds: number;
  /** Seconds to add for a range timer when it rings at the lower end; null if there is no more. */
  extraSeconds: number | null;
  /** Milliseconds left while paused, else null. */
  pausedLeft: number | null;
}

/** The JSON stored under KEY; null if there is none or it is broken. */
function readStored(key: string): unknown {
  try {
    return JSON.parse(localStorage.getItem(key) ?? "null");
  }
  catch {
    return null;
  }
}

/** The stored list; broken or foreign data counts as no timers. */
function loadTimers(): KhTimer[] {
  const stored = readStored(STORAGE_KEY);
  return Array.isArray(stored) ? stored : [];
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

  /** Starts a timer for TIME, named LABEL, started in step STEP (0-based) of the recipe RECIPESLUG. */
  function start(time: KhTime, label: string, recipeSlug: string, step: number): KhTimer {
    const extraSeconds = time.upperSeconds === null ? null : time.upperSeconds - time.seconds;
    timers.value.push({ id: uuid4(), label, recipeSlug, step, endsAt: now() + time.seconds * 1000, seconds: time.seconds, extraSeconds, pausedLeft: null });
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

/** Removes all timers, in the list and in storage (at sign-out, so a shared device keeps none). */
export function clearKhTimers(): void {
  timers.value = [];
}

/** The address of the recipe TIMER belongs to, at the step it was started in. */
export function timerRecipePath(groupSlug: string, timer: KhTimer): string {
  return `/g/${groupSlug}/r/${timer.recipeSlug}?step=${timer.step + 1}`;
}

/** SECONDS as m:ss, or h:mm:ss from an hour on. */
export function formatTimeLeft(seconds: number): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const hours = Math.floor(seconds / 3600);
  const rest = `${hours ? pad(Math.floor(seconds / 60) % 60) : Math.floor(seconds / 60)}:${pad(seconds % 60)}`;
  return hours ? `${hours}:${rest}` : rest;
}

let audio: AudioContext | undefined;

/** Allows sounds: iOS only plays Web Audio that was started by a tap, so call this from a tap. */
export function unlockAudio(): void {
  // The "playback" channel ignores the iPhone's mute switch (Safari 17+); without it the alarm stays silent there.
  const session = (navigator as Navigator & { audioSession?: { type: string } }).audioSession;
  if (session) session.type = "playback";
  audio ??= new AudioContext();
  void audio.resume();
}

/** One short beep, if sound was unlocked; wakes the audio context if iOS has suspended it. */
function beep(): void {
  if (!audio) return;
  if (audio.state !== "running") void audio.resume();
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

let alarmScope: EffectScope | undefined;
/** True while the step view lists the timers itself; the app-wide bar then stays away. */
export const timersListedInStep = ref(false);

/** Makes a due timer ring on every page: the one app-wide alarm, rung from the first timer running out until none
 * is left, and again whenever a further timer runs out. Safe to call from many places; only the first call sets it up, so there is never a second alarm. */
export function useKhAlarm(): void {
  if (alarmScope) return;
  const { ringing } = useKhTimers();
  let stopAlarm: (() => void) | undefined;
  // Own scope, so the alarm outlives the component that happened to start it.
  alarmScope = effectScope(true);
  alarmScope.run(() => {
    // After a reload no tap has unlocked sound yet; the first tap anywhere does. Safari counts only the end of a tap
    // (touchend, click) as the user's permission for sound, not pointerdown.
    document.addEventListener("touchend", unlockAudio, { once: true });
    document.addEventListener("click", unlockAudio, { once: true });
    // A timer that runs out while another is still ringing restarts the alarm, which may have timed out meanwhile.
    watch(() => ringing.value.map(timer => timer.id), (ids, oldIds = []) => {
      if (!ids.length) {
        stopAlarm?.();
        stopAlarm = undefined;
      }
      else if (!stopAlarm || ids.some(id => !oldIds.includes(id))) {
        stopAlarm?.();
        stopAlarm = startAlarm();
      }
    }, { immediate: true });
  });
}

/** The address that starts an iOS Shortcut named NAME with the minutes (rounded up) for the clock app's timer. */
export function clockTimerUrl(name: string, seconds: number): string {
  return `shortcuts://run-shortcut?name=${encodeURIComponent(name)}&input=text&text=${Math.ceil(seconds / 60)}`;
}

/**
 * Whether this device can run an iOS Shortcut: iPhone and iPad only. iPadOS Safari names itself "Macintosh", so a Mac
 * name with a touch screen counts as an iPad. Android has no Shortcuts app, and browsers there cannot start its timer.
 */
export function offersClockShortcut(userAgent: string, touchPoints: number): boolean {
  return /iPhone|iPad|iPod/.test(userAgent) || (/Macintosh/.test(userAgent) && touchPoints > 1);
}

interface ClockSetting {
  enabled: boolean;
  name: string;
}

/** The stored clock setting; anything missing or broken is replaced by the standard. */
function loadClock(): ClockSetting {
  const stored = readStored(CLOCK_KEY) as Partial<ClockSetting> | null;
  return {
    enabled: stored?.enabled === true,
    name: typeof stored?.name === "string" && stored.name ? stored.name : DEFAULT_CLOCK_SHORTCUT,
  };
}

const clock = ref(loadClock());
watch(clock, setting => localStorage.setItem(CLOCK_KEY, JSON.stringify(setting)), { deep: true, flush: "sync" });

/** Whether this device offers "Auf Uhr-Timer legen", and the name of its Shortcut; kept on the device. `offered`
 * says whether the device can run it at all, so a switch left on from before (say on Android) shows no button. */
export function useKhClockSetting() {
  const offered = offersClockShortcut(navigator.userAgent, navigator.maxTouchPoints);
  return { enabled: toRef(clock.value, "enabled"), name: toRef(clock.value, "name"), offered };
}
