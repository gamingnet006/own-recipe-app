// KH: the rules of the voice commands in cook mode (P7.5) without microphone or model: which spoken words mean which
// command, the grammar the recognizer is limited to, and the errors the screen can name.

export type VoiceCommand = "next" | "back" | "timer" | "stop";

/** The spoken words and what they do; the synonyms help where "weiter" is hard to tell from other words. */
const WORDS: Record<string, VoiceCommand> = {
  weiter: "next",
  nächster: "next",
  zurück: "back",
  vorher: "back",
  timer: "timer",
  stopp: "stop",
};

/** Where the app serves the German model (docker/Dockerfile puts it there; never fetched from a third party). */
export const VOICE_MODEL_URL = "/kh-models/vosk-model-small-de-0.15.tar.gz";

/** The words the recognizer may hear, as the JSON list Vosk takes; "[unk]" takes everything else. */
export const VOICE_GRAMMAR = JSON.stringify([...Object.keys(WORDS), "[unk]"]);

/** The command in TEXT as the recognizer heard it (the first known word wins), or null if there is none. */
export function commandOf(text: string): VoiceCommand | null {
  for (const word of text.toLowerCase().split(/\s+/)) {
    const command = WORDS[word];
    if (command) return command;
  }
  return null;
}

/** Why listening could not start: no microphone allowed, a browser without the needed parts, or no usable model.
 * CODE picks the text `kh.voice.error-<code>`. */
export class VoiceError extends Error {
  constructor(readonly code: "mic-denied" | "unsupported" | "model") {
    super(code);
  }
}

/** Starts listening and calls ONTEXT with every phrase; ONPROGRESS gets 0 to 100 while the model loads. Resolves when
 * listening, with the way to stop; rejects with a VoiceError. */
export type VoiceStarter = (onText: (text: string) => void, onProgress: (percent: number) => void) => Promise<{ stop: () => void }>;
