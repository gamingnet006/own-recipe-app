// KH: tests for accounts without e-mail and first sign-in (D53): placeholder addresses, the redirect to the first
// steps, the server's error text, and that choosing a password sets the new token.
import { beforeEach, describe, expect, test, vi } from "vitest";
import { failureText, isPlaceholderEmail, onboardingRedirect, shownEmail } from "../lib/onboarding";
import { khOnboarding, useKhOnboarding } from "../composables/use-kh-onboarding";

const getMock = vi.hoisted(() => vi.fn());
const postMock = vi.hoisted(() => vi.fn());
const setToken = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, post: postMock }) }));
vi.mock("~/composables/use-auth-backend", () => ({ useAuthBackend: () => ({ setToken }) }));

const status = (mustChangePassword: boolean, needsEmail: boolean) => ({ mustChangePassword, needsEmail, pendingEmail: null });

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  setToken.mockReset();
  khOnboarding.status = null;
  khOnboarding.userId = "";
});

describe("placeholder addresses", () => {
  test("every .invalid address counts as no e-mail", () => {
    expect(isPlaceholderEmail("a1b2c3d4e5f6a7b8@no-email.invalid")).toBe(true);
    expect(isPlaceholderEmail("x@linked-account.invalid")).toBe(true);
    expect(isPlaceholderEmail("Anna@Example.com")).toBe(false);
    expect(isPlaceholderEmail("")).toBe(false);
  });

  test("shownEmail is empty for placeholders and missing values", () => {
    expect(shownEmail("a@no-email.invalid")).toBe("");
    expect(shownEmail(null)).toBe("");
    expect(shownEmail("anna@example.com")).toBe("anna@example.com");
  });
});

describe("onboardingRedirect", () => {
  test("sends people with open steps to the first steps", () => {
    expect(onboardingRedirect("/g/home", status(true, false))).toBe("/erste-schritte");
    expect(onboardingRedirect("/g/home", status(false, true))).toBe("/erste-schritte");
  });

  test("leaves everyone else and the exempt pages alone", () => {
    expect(onboardingRedirect("/g/home", status(false, false))).toBeNull();
    expect(onboardingRedirect("/g/home", null)).toBeNull();
    for (const path of ["/erste-schritte", "/login", "/logout", "/willkommen", "/email-bestaetigen"]) {
      expect(onboardingRedirect(path, status(true, true))).toBeNull();
    }
  });
});

describe("failureText", () => {
  test("shows the server's detail, else the fallback", () => {
    expect(failureText({ response: { data: { detail: "Mail sending is not set up" } } }, "x")).toBe("Mail sending is not set up");
    expect(failureText({ response: { data: { detail: [{ msg: "bad" }] } } }, "fallback")).toBe("fallback");
    expect(failureText(null, "fallback")).toBe("fallback");
  });
});

describe("useKhOnboarding", () => {
  test("loads the status once per user", async () => {
    getMock.mockResolvedValue({ data: status(true, false) });
    const { loadFor } = useKhOnboarding();
    await loadFor("u1");
    await loadFor("u1");
    expect(getMock).toHaveBeenCalledTimes(1);
    expect(khOnboarding.status?.mustChangePassword).toBe(true);
    await loadFor("u2");
    expect(getMock).toHaveBeenCalledTimes(2);
  });

  test("a failed request leaves the app unblocked", async () => {
    getMock.mockResolvedValue({ data: null, error: new Error("down") });
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    await useKhOnboarding().loadFor("u1");
    expect(khOnboarding.status).toBeNull();
    expect(errorSpy).toHaveBeenCalled();
  });

  test("choosing the password sets the new token before the status is read again", async () => {
    postMock.mockResolvedValue({ data: { access_token: "new", token_type: "bearer" } });
    getMock.mockImplementation(() => {
      expect(setToken).toHaveBeenCalledWith("new");
      return Promise.resolve({ data: status(false, false) });
    });
    const { setPassword } = useKhOnboarding();
    expect(await setPassword("longenough", "fb")).toBeNull();
    expect(postMock).toHaveBeenCalledWith("/api/kh/onboarding/password", { password: "longenough" }, { suppressAlert: true });
    expect(khOnboarding.status?.mustChangePassword).toBe(false);
  });

  test("a refused password returns the server's text and keeps the token", async () => {
    postMock.mockResolvedValue({ data: null, error: { response: { data: { detail: "too short" } } } });
    expect(await useKhOnboarding().setPassword("short", "fb")).toBe("too short");
    expect(setToken).not.toHaveBeenCalled();
  });
});
