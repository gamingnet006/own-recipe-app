// KH: tests for the import from a share sheet (D57): the query read into link and text, the cut at the draft limit,
// and the round trip through the login, which has to keep the query.
import { describe, expect, test, vi } from "vitest";
import { hasSharedImport, readSharedImport } from "../lib/shared-import";

const navigateTo = vi.hoisted(() => vi.fn((to: unknown, options?: unknown) => ({ to, options })));
vi.stubGlobal("defineNuxtRouteMiddleware", (fn: unknown) => fn);
vi.stubGlobal("navigateTo", navigateTo);

describe("readSharedImport", () => {
  test("the same address twice is one link, all its copies are removed before the length check", () => {
    const link = "https://a.de/r";
    expect(readSharedImport({ recipe_import_text: `Schau: ${link} ${link}` }, 500)).toEqual({ link, text: "" });
    const long = `${"x".repeat(150)} ${link} ${"y".repeat(150)}`;
    expect(readSharedImport({ recipe_import_text: long }, 500).link).toBe("");
    expect(readSharedImport({ recipe_import_text: `${link} https://b.de` }, 500).link).toBe("");
  });

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

  test("a short app message around one address becomes the link (Chefkoch, Rezeptwelt share like this)", () => {
    expect(readSharedImport({ recipe_import_text: "Schau mal: Grießpudding https://www.chefkoch.de/rezepte/1/x.html." }, 500))
      .toEqual({ link: "https://www.chefkoch.de/rezepte/1/x.html", text: "" });
    expect(readSharedImport({ recipe_import_text: "Muffins (https://a.de/r)" }, 500).link).toBe("https://a.de/r");
  });

  test("other texts stay texts: a recipe with a source address, two addresses, other schemes, an explicit link", () => {
    const recipe = `Grießpudding\n${"500 ml Milch, 60 g Grieß, 2 Eigelbe. ".repeat(8)}\nQuelle: https://a.de/r`;
    expect(readSharedImport({ recipe_import_text: recipe }, 1000)).toEqual({ link: "", text: recipe });
    expect(readSharedImport({ recipe_import_text: "https://a.de/1 oder https://b.de/2" }, 100).link).toBe("");
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
