// KH: the state of the voice commands in cook mode (P7.5): off, loading the model, listening; the last word heard and
// a readable error. START is replaceable for tests.
import { onBeforeUnmount, ref } from "vue";
import { commandOf, VoiceError, type VoiceCommand, type VoiceStarter } from "../lib/voice";
import { startVosk } from "../lib/voice-vosk";

/** Switches listening on and off; ONCOMMAND gets every command that was heard. */
export function useKhVoice(onCommand: (command: VoiceCommand) => void, start: VoiceStarter = startVosk) {
  const status = ref<"off" | "loading" | "listening">("off");
  const progress = ref(0);
  const heard = ref("");
  const error = ref<VoiceError["code"] | null>(null);
  let session: { stop: () => void } | null = null;
  // Counts the taps, so a stop during loading is not undone when the model arrives.
  let round = 0;

  function stop(): void {
    round++;
    session?.stop();
    session = null;
    status.value = "off";
  }

  async function startListening(): Promise<void> {
    const mine = ++round;
    error.value = null;
    heard.value = "";
    progress.value = 0;
    status.value = "loading";
    try {
      const started = await start((text) => {
        const command = commandOf(text);
        if (!command) return;
        heard.value = text;
        onCommand(command);
      }, percent => (progress.value = percent));
      if (mine !== round) return started.stop();
      session = started;
      status.value = "listening";
    }
    catch (e) {
      if (mine !== round) return;
      error.value = e instanceof VoiceError ? e.code : "model";
      status.value = "off";
    }
  }

  onBeforeUnmount(stop);

  return { status, progress, heard, error, toggle: () => (status.value === "off" ? startListening() : stop()) };
}
