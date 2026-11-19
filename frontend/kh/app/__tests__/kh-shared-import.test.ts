// KH: tests for the import from a share sheet (D57): the query read into link and text, the cut at the draft limit,
// and the round trip through the login, which has to keep the query.
import { describe, expect, test, vi } from "vitest";
import { hasSharedImport, readSharedImport } from "../lib/shared-import";

const navigateTo = vi.hoisted(() => vi.fn((to: unknown, options?: unknown) => ({ to, options })));
vi.stubGlobal("defineNuxtRouteMiddleware", (fn: unknown) => fn);
vi.stubGlobal("navigateTo", navigateTo);

describe("readSharedImport", () => {
  test("reads a link and a text", () => {
    expect(readSharedImport({ recipe_import_url: "https://a.de/r" }, 100)).toEqual({ link: "https://a.de/r", text: "" });
    expect(readSharedImport({ recipe_import_text: "Hallo" }, 100)).toEqual({ link: "", text: "Hallo" });
  });

  test("gives empty values without a query and takes the first of a repeated one", () => {
    expect(readSharedImport({}, 100)).toEqual({ link: "", text: "" });
    expect(readSharedImport({ recipe_import_text: ["eins", "zwei"] }, 100).text).toBe("eins");
    expect(readSharedImport({ recipe_import_text: null }, 100).text).toBe("");
  });

  test("a text that is just a web address becomes the link, however it is padded", () => {
    expect(readSharedImport({ recipe_import_text: " https://a.de/r?x=1\n" }, 100)).toEqual({ link: "https://a.de/r?x=1", text: "" });
    expect(readSharedImport({ recipe_import_text: "http://a.de" }, 100).link).toBe("http://a.de");
  });

  test("other texts stay texts: a sentence with an address, other schemes, an explicit link", () => {
    expect(readSharedImport({ recipe_import_text: "Probier das: https://a.de/r" }, 100).link).toBe("");
    expect(readSharedImport({ recipe_import_text: "ftp://a.de/r" }, 100).link).toBe("");
    expect(readSharedImport({ recipe_import_text: "Hallo" }, 100).link).toBe("");
    expect(readSharedImport({ recipe_import_url: "https://a.de/1", recipe_import_text: "https://b.de/2" }, 100))
      .toEqual({ link: "https://a.de/1", text: "https://b.de/2" });
  });

  test("cuts a long text at the draft limit", () => {
    expect(readSharedImport({ recipe_import_text: "abcdef" }, 4).text).toBe("abcd");
  });
});

describe("hasSharedImport", () => {
  test("knows both parameters", () => {
    expect(hasSharedImport({ recipe_import_url: "x" })).toBe(true);
    expect(hasSharedImport({ recipe_import_text: "x" })).toBe(true);
    expect(hasSharedImport({ other: "x" })).toBe(false);
  });
});

describe("the share target's redirects keep the text", () => {
  const to = { path: "/r/create/url", fullPath: "/r/create/url?recipe_import_text=Hallo%20Welt%20%26%20mehr" };

  test("signed out: the login gets the whole path as its redirect and gives it back unchanged", async () => {
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: null } }));
    const { default: middleware } = await import("../../../app/middleware/pwa-share-target-redirect.global");
    (middleware as (to: unknown) => unknown)(to);
    const target = navigateTo.mock.calls.at(-1)![0] as string;
    const redirect = new URL(target, "http://x").searchParams.get("redirect"); // what vue-router hands the login page
    expect(redirect).toBe(to.fullPath);
  });

  test("signed in: the group path keeps the query, and the drafts redirect keeps it too", async () => {
    vi.stubGlobal("useMealieAuth", () => ({ user: { value: { groupSlug: "home" } } }));
    const { default: middleware } = await import("../../../app/middleware/pwa-share-target-redirect.global");
    (middleware as (to: unknown) => unknown)(to);
    expect(navigateTo.mock.calls.at(-1)![0]).toBe(`/g/home${to.fullPath}`);

    const { default: khRedirect } = await import("../middleware/kh-import-redirect.global");
    const query = { recipe_import_text: "Hallo Welt & mehr" };
    (khRedirect as (to: unknown) => unknown)({ path: "/g/home/r/create/url", query });
    expect(navigateTo.mock.calls.at(-1)![0]).toEqual({ path: "/g/home/drafts", query });
  });
});
