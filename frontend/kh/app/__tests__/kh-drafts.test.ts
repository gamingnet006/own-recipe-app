// KH: tests for the drafts UI logic (phase 2): which Mealie import pages lead to the intake, the review
// layout on phone and iPad, the texts for error codes and origins, and the drafts counter in the menu.
import { afterEach, describe, expect, test, vi } from "vitest";
import type { KhOrigin } from "../lib/api/drafts";
import { errorText, importRedirectTarget, originLabel, reviewLayout, useKhDraftCount } from "../composables/use-kh-drafts";
import de from "../../lang/de-DE.json";
import en from "../../lang/en-US.json";

const getMock = vi.hoisted(() => vi.fn());

vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock }) }));

const t = (key: string) => key;

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
      expect(importRedirectTarget(`/g/familie/r/create/${page}`)).toBe("/g/familie/drafts/new");
    }
    expect(importRedirectTarget("/g/familie/r/create/ai/")).toBe("/g/familie/drafts/new");
  });

  test("leaves typing a recipe yourself and the zip import alone", () => {
    expect(importRedirectTarget("/g/familie/r/create/new")).toBeNull();
    expect(importRedirectTarget("/g/familie/r/create/zip")).toBeNull();
  });
});

describe("texts", () => {
  test("an unknown error code gets the general error text", () => {
    expect(errorText("quota_exceeded", t)).toBe(t("kh.drafts.error.quota_exceeded"));
    expect(errorText("something_new", t)).toBe(t("kh.drafts.error.unknown"));
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
