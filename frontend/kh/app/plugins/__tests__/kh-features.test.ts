// KH: tests the plugin that loads Küchenhelfer's switches: it passes the answer on, and without
// an answer every hidden Mealie part stays hidden and the error is reported.
import { afterEach, describe, expect, test, vi } from "vitest";

const getMock = vi.hoisted(() => vi.fn());

vi.mock("axios", () => ({ default: { get: getMock } }));

type FeaturesPlugin = { setup: () => Promise<{ provide: { khFeatures: { shareLinks: boolean } } }> };

async function loadFeatures() {
  vi.stubGlobal("defineNuxtPlugin", (plugin: unknown) => plugin);
  const plugin = (await import("../kh-features.client")).default as unknown as FeaturesPlugin;
  return (await plugin.setup()).provide.khFeatures;
}

afterEach(() => {
  getMock.mockReset();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("kh-features plugin", () => {
  test("passes the switches on", async () => {
    getMock.mockResolvedValue({ data: { shareLinks: true } });

    expect(await loadFeatures()).toEqual({ shareLinks: true, noticePollMinutes: 5 });
    expect(getMock).toHaveBeenCalledWith("/api/kh/features");
  });

  test("keeps everything hidden without an answer", async () => {
    getMock.mockRejectedValue(new Error("offline"));
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(await loadFeatures()).toEqual({ shareLinks: false, noticePollMinutes: 5 });
    expect(errorSpy).toHaveBeenCalled();
  });
});
