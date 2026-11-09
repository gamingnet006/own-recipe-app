// KH: the real listener of the voice commands (P7.5): the microphone into Vosk (WebAssembly, in a worker) with the
// German model served by the app itself. Everything stays on the device; the logic around it is in voice.ts.
import { VoiceError, VOICE_GRAMMAR, VOICE_MODEL_URL, type VoiceStarter } from "./voice";

/** Downloads URL as an object address the worker can load, reporting 0 to 100 on the way (the size comes from the
 * Content-Length; without it only the end is reported). */
export async function fetchWithProgress(url: string, onProgress: (percent: number) => void, fetcher: typeof fetch = fetch): Promise<string> {
  const response = await fetcher(url);
  if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
  const total = Number(response.headers.get("Content-Length")) || 0;
  const reader = response.body.getReader();
  const parts: BlobPart[] = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    parts.push(value as BlobPart);
    loaded += value.length;
    if (total) onProgress(Math.min(100, Math.round((loaded / total) * 100)));
  }
  onProgress(100);
  return URL.createObjectURL(new Blob(parts));
}

/** Opens the microphone (the tap that calls this allows it), loads the model and feeds the recognizer. */
export const startVosk: VoiceStarter = async (onText, onProgress) => {
  if (!navigator.mediaDevices?.getUserMedia || typeof WebAssembly === "undefined" || typeof Worker === "undefined") {
    throw new VoiceError("unsupported");
  }
  // Made right in the tap, because iOS only lets an audio context start from one.
  const context = new AudioContext();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } })
    .catch(() => {
      void context.close();
      throw new VoiceError("mic-denied");
    });
  const closeMic = () => {
    stream.getTracks().forEach(track => track.stop());
    void context.close();
  };
  let modelAddress = "";
  try {
    modelAddress = await fetchWithProgress(VOICE_MODEL_URL, onProgress);
    const vosk = await import("vosk-browser");
    const model = await vosk.createModel(modelAddress);
    const recognizer = new model.KaldiRecognizer(context.sampleRate, VOICE_GRAMMAR);
    recognizer.on("result", message => onText((message as { result: { text: string } }).result.text));
    // ponytail: ScriptProcessor is deprecated but works on every browser, iOS included; AudioWorklet if it ever goes
    const processor = context.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = event => recognizer.acceptWaveform(event.inputBuffer);
    context.createMediaStreamSource(stream).connect(processor);
    // The node must be connected to something to run; it outputs silence.
    processor.connect(context.destination);
    return {
      stop: () => {
        processor.disconnect();
        recognizer.remove();
        model.terminate();
        closeMic();
      },
    };
  }
  catch (error) {
    closeMic();
    console.error("Küchenhelfer: voice model failed", error);
    throw new VoiceError("model");
  }
  finally {
    if (modelAddress) URL.revokeObjectURL(modelAddress);
  }
};
