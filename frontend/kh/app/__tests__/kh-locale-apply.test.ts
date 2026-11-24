// KH: tests for showing and choosing the language: the account's choice, the device's language, the installation's
// language only when the device speaks neither German nor English, and saving only when signed in.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { applyKhLocale, chooseKhLocale, resetKhLocale } from "../composables/use-kh-locale";

const installationLocale = vi.hoisted(() => vi.fn());
const saveKhLocale = vi.hoisted(() => vi.fn());

vi.mock("../lib/api/onboarding", () => ({ KhOnboardingApi: class { installationLocale = installationLocale; } }));
vi.mock("../composables/use-kh-sidebar", () => ({ saveKhLocale }));
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({}) }));
vi.mock("~/composables/use-global-i18n", () => ({ useGlobalI18n: () => ({}) }));

const setLocale = vi.fn();
const i18n = { setLocale } as never;

function device(...languages: string[]) {
  vi.stubGlobal("navigator", { languages, language: languages[0] });
}

beforeEach(() => {
  setLocale.mockReset();
  installationLocale.mockReset();
  saveKhLocale.mockReset();
  resetKhLocale();
});

describe("applyKhLocale", () => {
  test("the account's choice wins over the device and asks nothing", async () => {
    device("de-DE");
    await applyKhLocale("en-US", i18n);
    expect(setLocale).toHaveBeenCalledWith("en-US");
    expect(installationLocale).not.toHaveBeenCalled();
  });

  test("without a choice the device's German or English is used", async () => {
    device("fr-FR", "de-AT");
    await applyKhLocale(null, i18n);
    expect(setLocale).toHaveBeenCalledWith("de-DE");
    expect(installationLocale).not.toHaveBeenCalled();
  });

  test("another device language falls back to the installation's, asked once, else English", async () => {
    device("fr-FR");
    installationLocale.mockResolvedValue({ data: { locale: "de-DE" } });
    await applyKhLocale(null, i18n);
    await applyKhLocale(null, i18n);
    expect(setLocale).toHaveBeenLastCalledWith("de-DE");
    expect(installationLocale).toHaveBeenCalledTimes(1);
    resetKhLocale();
    installationLocale.mockResolvedValue({ data: null });
    await applyKhLocale(null, i18n);
    expect(setLocale).toHaveBeenLastCalledWith("en-US");
  });
});

describe("chooseKhLocale", () => {
  test("shows the language and keeps it on the account only when signed in", async () => {
    await chooseKhLocale("en-US", true, i18n);
    expect(setLocale).toHaveBeenCalledWith("en-US");
    expect(saveKhLocale).toHaveBeenCalledWith("en-US");
    saveKhLocale.mockClear();
    await chooseKhLocale("de-DE", false, i18n);
    expect(saveKhLocale).not.toHaveBeenCalled();
  });
});
