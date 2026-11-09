// KH: tests for the voice commands of cook mode (P7.5): the word-to-command rule, and the component with a fake
// recognizer (the real one needs a microphone and a 45 MB model) driving the steps and the timers.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { reactive } from "vue";
import KhCookVoice from "../components/KhCookVoice.vue";
import { commandOf, VOICE_MODEL_BYTES, VoiceError } from "../lib/voice";
import { fetchWithProgress } from "../lib/voice-vosk";
import { khAddons } from "../composables/use-kh-addons";
import { useKhCook } from "../composables/use-kh-cook";
import { clearKhTimers, useKhTimers } from "../composables/use-kh-timers";
import { i18n } from "~/tests/setup";
import en from "../../lang/en-US.json";
import de from "../../lang/de-DE.json";
import type { Recipe } from "~/lib/api/types/recipe";

i18n.global.mergeLocaleMessage("en-US", en);

const startMock = vi.hoisted(() => vi.fn());
vi.mock("../lib/voice-vosk", async importOriginal => ({ ...(await importOriginal<typeof import("../lib/voice-vosk")>()), startVosk: startMock }));

describe("commandOf", () => {
  test.each([
    ["weiter", "next"],
    ["nächster", "next"],
    ["zurück", "back"],
    ["vorher", "back"],
    ["timer", "timer"],
    ["stopp", "stop"],
  ])("%s is %s", (text, command) => expect(commandOf(text)).toBe(command));

  test("ignores case, spaces and other words", () => {
    expect(commandOf("  Weiter ")).toBe("next");
    expect(commandOf("bitte weiter")).toBe("next");
    expect(commandOf("[unk] zurück")).toBe("back");
  });

  test("nothing known is null", () => {
    expect(commandOf("")).toBeNull();
    expect(commandOf("   ")).toBeNull();
    expect(commandOf("hallo welt")).toBeNull();
  });
});

describe("the voice texts", () => {
  test("every key exists in German and English", () => {
    expect(Object.keys(de.kh.voice).sort()).toEqual(Object.keys(en.kh.voice).sort());
  });
});

describe("KhCookVoice", () => {
  const Button = { emits: ["click"], template: `<button @click="$emit('click')"><slot /></button>` };
  const recipe = {
    slug: "suppe",
    recipeIngredient: [],
    recipeInstructions: [{ id: "1", text: "Zwiebeln anbraten." }, { id: "2", text: "10 Minuten kochen." }, { id: "3", text: "Servieren." }],
  } as unknown as Recipe;
  const query = reactive<Record<string, string>>({});
  let said: (text: string) => void;
  const stopMock = vi.fn();

  function render(flags: { voice: boolean } = { voice: true }) {
    khAddons.enabled = { ...khAddons.enabled, ...flags };
    const cook = useKhCook(() => 3);
    const close = vi.fn();
    const wrapper = mount(KhCookVoice, {
      props: { recipe, scale: 1, cook },
      attrs: { onClose: close },
      global: { stubs: { VBtn: Button, VIcon: true }, mocks: { $globals: { icons: { microphone: "mic" } } } },
    });
    return { wrapper, cook, close };
  }
  const toggle = (wrapper: ReturnType<typeof render>["wrapper"]) => wrapper.find("button");

  beforeEach(() => {
    vi.stubGlobal("AudioContext", class { resume = () => Promise.resolve(); });
    vi.stubGlobal("useRoute", () => ({ query }));
    vi.stubGlobal("useRouter", () => ({ replace: (to: { query: Record<string, string> }) => Object.assign(query, to.query) }));
    delete query.step;
    clearKhTimers();
    stopMock.mockReset();
    startMock.mockReset();
    startMock.mockImplementation(async (onText: (text: string) => void) => {
      said = onText;
      return { stop: stopMock };
    });
  });

  test("no button while the add-on is off", () => {
    expect(render({ voice: false }).wrapper.find("button").exists()).toBe(false);
  });

  test("nothing listens before the tap", () => {
    render();
    expect(startMock).not.toHaveBeenCalled();
  });

  test("weiter and zurück move through the steps; weiter on the last one closes", async () => {
    const { wrapper, cook, close } = render();
    await toggle(wrapper).trigger("click");
    await flushPromises();
    said("weiter");
    said("weiter");
    expect(cook.step.value).toBe(2);
    said("zurück");
    expect(cook.step.value).toBe(1);
    said("weiter");
    said("weiter");
    expect(close).toHaveBeenCalledOnce();
  });

  test("timer starts the first time of the current step, once per word", async () => {
    const { wrapper, cook } = render();
    await toggle(wrapper).trigger("click");
    await flushPromises();
    said("timer");
    expect(useKhTimers().timers.value).toHaveLength(0);
    cook.goTo(1);
    said("timer");
    const [timer] = useKhTimers().timers.value;
    expect(timer).toMatchObject({ seconds: 600, step: 1, recipeSlug: "suppe" });
  });

  test("stopp silences every ringing timer and leaves running ones", async () => {
    const { wrapper } = render();
    const timers = useKhTimers();
    const rung = timers.start({ start: 0, end: 1, text: "a", seconds: -5, upperSeconds: null }, "a", "suppe", 0);
    const running = timers.start({ start: 0, end: 1, text: "b", seconds: 600, upperSeconds: null }, "b", "suppe", 0);
    await toggle(wrapper).trigger("click");
    await flushPromises();
    said("stopp");
    expect(timers.timers.value.map(t => t.id)).toEqual([running.id]);
    expect(rung.id).not.toBe(running.id);
  });

  test("shows the last heard word and the loading state", async () => {
    let ready!: () => void;
    startMock.mockImplementation(async (onText: (text: string) => void, onProgress: (percent: number) => void) => {
      said = onText;
      onProgress(40);
      await new Promise<void>(resolve => (ready = resolve));
      return { stop: stopMock };
    });
    const { wrapper } = render();
    await toggle(wrapper).trigger("click");
    expect(wrapper.text()).toContain(`${en.kh.voice.loading} 40 %`);
    ready();
    await flushPromises();
    expect(wrapper.text()).toContain(en.kh.voice.listening);
    said("hallo weiter");
    await flushPromises();
    expect(wrapper.text()).toContain("weiter");
  });

  test("the second tap stops the microphone", async () => {
    const { wrapper } = render();
    await toggle(wrapper).trigger("click");
    await flushPromises();
    await toggle(wrapper).trigger("click");
    expect(stopMock).toHaveBeenCalledOnce();
    expect(wrapper.text()).not.toContain(en.kh.voice.listening);
  });

  test.each([
    ["mic-denied", en.kh.voice["error-mic-denied"]],
    ["unsupported", en.kh.voice["error-unsupported"]],
    ["model", en.kh.voice["error-model"]],
  ])("a %s failure is shown as a readable text", async (code, text) => {
    startMock.mockRejectedValue(new VoiceError(code as "model"));
    const { wrapper } = render();
    await toggle(wrapper).trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain(text);
  });
});

describe("fetchWithProgress", () => {
  const chunk = (n: number) => new Uint8Array(n);
  const reply = (chunks: Uint8Array[], length: string | null, ok = true) => vi.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 404,
    headers: { get: () => length },
    body: { getReader: () => { const rest = [...chunks]; return { read: async () => (rest.length ? { done: false, value: rest.shift() } : { done: true }) }; } },
  });

  beforeEach(() => vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: () => "blob:model" })));

  test("reports the percent per chunk and returns an address", async () => {
    const seen: number[] = [];
    const url = await fetchWithProgress("/m", p => seen.push(p), reply([chunk(25), chunk(75)], "100") as unknown as typeof fetch);
    expect(seen).toEqual([25, 100, 100]);
    expect(url).toBe("blob:model");
  });

  test("without a Content-Length the known model size drives the percent", async () => {
    const seen: number[] = [];
    await fetchWithProgress("/m", p => seen.push(p), reply([chunk(VOICE_MODEL_BYTES / 2)], null) as unknown as typeof fetch);
    expect(seen).toEqual([50, 100]);
  });

  test("an error answer fails", async () => {
    await expect(fetchWithProgress("/m", () => {}, reply([], null, false) as unknown as typeof fetch)).rejects.toThrow("HTTP 404");
  });
});
