// KH: tests for the drafts UI logic (phase 2): which Mealie import pages lead to the intake, the review
// layout on phone and iPad, the texts, the drafts counter, and how the list and the review behave.
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, test, vi } from "vitest";
import { defineComponent, h } from "vue";
import type { KhDraft, KhDraftWarning, KhOrigin } from "../lib/api/drafts";
import type { Recipe } from "~/lib/api/types/recipe";
import {
  approveTarget,
  draftTitle,
  errorText,
  importRedirectTarget,
  isVideoLink,
  originLabel,
  pollingNeeded,
  recipeChanges,
  requestError,
  reviewLayout,
  useKhDraftCount,
  useKhPolling,
  warningTarget,
} from "../composables/use-kh-drafts";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

const getMock = vi.hoisted(() => vi.fn());

vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock }) }));

const t = (key: string) => key;

function mountPage(load: () => Promise<boolean>) {
  return mount(defineComponent({
    setup() {
      useKhPolling(load);
      return () => h("div");
    },
  }));
}

function keys(messages: object, prefix = ""): string[] {
  return Object.entries(messages)
    .flatMap(([key, value]) => (typeof value === "object" ? keys(value, `${prefix}${key}.`) : [`${prefix}${key}`]))
    .sort();
}

afterEach(() => {
  getMock.mockReset();
});

describe("importRedirectTarget", () => {
  test("sends Mealie's import pages to the intake", () => {
    for (const page of ["url", "ai", "image", "html", "bulk"]) {
      expect(importRedirectTarget(`/g/familie/r/create/${page}`)).toBe("/g/familie/drafts");
    }
    expect(importRedirectTarget("/g/familie/r/create/ai/")).toBe("/g/familie/drafts");
  });

  test("the old intake address leads to the intake on the drafts page", () => {
    expect(importRedirectTarget("/g/familie/drafts/new")).toBe("/g/familie/drafts");
    expect(importRedirectTarget("/g/familie/drafts/new/")).toBe("/g/familie/drafts");
  });

  test("leaves the intake, a draft's review, typing a recipe yourself and the zip import alone", () => {
    expect(importRedirectTarget("/g/familie/drafts")).toBeNull();
    expect(importRedirectTarget("/g/familie/drafts/abc")).toBeNull();
    expect(importRedirectTarget("/g/familie/r/create/new")).toBeNull();
    expect(importRedirectTarget("/g/familie/r/create/zip")).toBeNull();
  });
});

describe("isVideoLink", () => {
  test("links to video sites and their subdomains are video links", () => {
    for (const url of ["https://www.instagram.com/reel/x", "https://vm.tiktok.com/a", "https://youtu.be/1",
      "https://m.youtube.com/watch?v=1", "https://fb.watch/x", "https://facebook.com/reel/1", "youtube.com/watch?v=1"]) {
      expect(isVideoLink(url)).toBe(true);
    }
  });

  test("other links and look-alikes are not", () => {
    for (const url of ["https://example.org/testkuchen", "https://example.org/instagram.com",
      "https://notyoutube.com/x", "", "not a link"]) {
      expect(isVideoLink(url)).toBe(false);
    }
  });

  test("the video link text is in both languages", () => {
    expect(de.kh.drafts.error.video_link).toBe(
      "Videos lädt Küchenhelfer nicht herunter. Füge die Beschreibung ein oder lade einen Screenshot hoch.",
    );
    expect(errorText("video_link", t)).toBe("kh.drafts.error.video_link");
  });
});

describe("texts", () => {
  test("an unknown error code gets the general error text", () => {
    expect(errorText("quota_exceeded", t)).toBe(t("kh.drafts.error.quota_exceeded"));
    expect(errorText("something_new", t)).toBe(t("kh.drafts.error.unknown"));
  });

  test("the recording errors have their own texts, a recording is titled by its file name", () => {
    for (const code of ["whisper_unreachable", "whisper_timeout", "whisper_failed", "media_too_large", "media_not_configured", "not_audio_video"]) {
      expect(errorText(code, t)).toBe(`kh.drafts.error.${code}`);
    }
    expect(draftTitle({ recipe: null, sourceUrl: null, sourceNote: "oma.m4a", sourceText: null } as KhDraft)).toBe("oma.m4a");
  });

  test("the origin names the source, the day and who added it", () => {
    const origin = { sourceType: "image", createdAt: "2026-10-31T09:30:00", userName: "Alex" } as KhOrigin;
    const day = () => "31.10.2026";
    expect(originLabel(origin, t, day)).toBe("kh.drafts.origin.image · 31.10.2026 · Alex");
    expect(originLabel({ ...origin, userName: "" }, t, day)).toBe("kh.drafts.origin.image · 31.10.2026");
  });

  test("German and English have the same texts", () => {
    expect(keys(de)).toEqual(keys(en));
  });
});

test("the review puts original and result side by side from iPad width", () => {
  expect(reviewLayout(390)).toBe("stacked");
  expect(reviewLayout(768)).toBe("side");
  expect(reviewLayout(820)).toBe("side");
});

describe("useKhDraftCount", () => {
  test("counts the open drafts and keeps the number when loading fails", async () => {
    const { count, refresh } = useKhDraftCount();
    getMock.mockResolvedValue({ data: [{ id: "a" }, { id: "b" }], error: null });
    await refresh();
    expect(count.value).toBe(2);

    getMock.mockResolvedValue({ data: null, error: new Error("offline") });
    await refresh();
    expect(count.value).toBe(2);
  });

  test("is shared by the menu and the pages", async () => {
    getMock.mockResolvedValue({ data: [{ id: "a" }], error: null });
    await useKhDraftCount().refresh();
    expect(useKhDraftCount().count.value).toBe(1);
  });
});

describe("drafts list and review", () => {
  test("a draft is named by its recipe, else its link, else the start of its text", () => {
    expect(draftTitle({ recipe: { name: "Testkuchen" } } as KhDraft)).toBe("Testkuchen");
    expect(draftTitle({ recipe: null, sourceUrl: "https://example.org/x" } as KhDraft)).toBe("example.org/x");
    expect(draftTitle({ recipe: null, sourceUrl: null, sourceText: "Testkuchen\n200 g Mehl" } as KhDraft)).toBe("Testkuchen");
    expect(draftTitle({ recipe: null, sourceUrl: null, sourceText: "a".repeat(80) } as KhDraft)).toBe(`${"a".repeat(60)}…`);
  });

  test("the list reloads while a draft is being recognized", () => {
    expect(pollingNeeded([{ status: "ready" }, { status: "working" }] as KhDraft[])).toBe(true);
    expect(pollingNeeded([{ status: "ready" }, { status: "failed" }] as KhDraft[])).toBe(false);
  });

  test("the review starts from the recognized servings and yield", () => {
    const recognized = { recipeServings: 4, recipeYieldQuantity: 1, recipeYield: "Springform Ø 26 cm" } as Recipe;
    expect(recipeChanges(recognized)).toEqual({ ...recognized, linkedSteps: [] });
    expect(recipeChanges(null)).toEqual({ recipeServings: 0, recipeYieldQuantity: 0, recipeYield: "", linkedSteps: [] });
  });

  test("the review starts with the step links the recognition made", () => {
    const link = { step: 0, start: 0, end: 5, text: "250 g", referenceId: "r", fraction: 1 };
    const stepAmounts = [{ ...link, linked: true }, { ...link, linked: false }, { ...link, linked: true }];
    const recognized = { khAmounts: { extras: [], stepAmounts } } as unknown as Recipe;
    expect(recipeChanges(recognized).linkedSteps).toEqual([0, 2]);
  });

  test("approving opens the recipe, in edit mode if asked", () => {
    expect(approveTarget("testkuchen", "familie", false)).toBe("/g/familie/r/testkuchen");
    expect(approveTarget("testkuchen", "familie", true)).toBe("/g/familie/r/testkuchen?edit=true");
  });

  test("amount warnings link nowhere", () => {
    const hint = { kind: "amount_unusual", name: "6000 g Mehl", recipeSlug: null, draftId: null } as KhDraftWarning;
    expect(warningTarget(hint, "g")).toBe("");
  });

  test("a hint links to the recipe or to the other draft", () => {
    const hint = { kind: "duplicate_link", name: "Testkuchen", recipeSlug: null, draftId: "d1" } as KhDraftWarning;
    expect(warningTarget(hint, "familie")).toBe("/g/familie/drafts/d1");
    expect(warningTarget({ ...hint, recipeSlug: "testkuchen", draftId: null }, "familie")).toBe("/g/familie/r/testkuchen");
  });

  test("a failed request gives its code, anything else counts as unknown", () => {
    const conflict = { response: { data: { detail: { code: "duplicates", warnings: [] } } } };
    expect(requestError(conflict)).toEqual({ code: "duplicates", warnings: [] });
    expect(requestError({ response: { data: { detail: "Not Found" } } }).code).toBe("unknown");
    expect(requestError(new Error("offline")).code).toBe("unknown");
  });

  test("a request that never reached the server counts as offline", () => {
    expect(requestError({ isAxiosError: true, message: "Network Error" }).code).toBe("offline");
    expect(errorText("offline", t)).toBe(t("kh.drafts.error.offline"));
  });
});

describe("useKhPolling", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  test("looks again every 3 seconds while needed and stops when the page is left", async () => {
    vi.useFakeTimers();
    const load = vi.fn(async () => true);
    const page = mountPage(load);
    await vi.advanceTimersByTimeAsync(0);
    expect(load).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(3000);
    expect(load).toHaveBeenCalledTimes(2);

    page.unmount();
    await vi.advanceTimersByTimeAsync(9000);
    expect(load).toHaveBeenCalledTimes(2);
  });

  test("stops once nothing is being recognized", async () => {
    vi.useFakeTimers();
    const load = vi.fn(async () => false);
    mountPage(load);
    await vi.advanceTimersByTimeAsync(9000);
    expect(load).toHaveBeenCalledTimes(1);
  });
});
