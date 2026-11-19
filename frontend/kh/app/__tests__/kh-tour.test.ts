// KH: tests for the first-sign-in tour (D59): the step list filtered by the add-ons, the decision when to show it, and
// that every step has its text in both languages.
import { describe, expect, test } from "vitest";
import { DEFAULT_ADDONS } from "../lib/addons";
import { shouldShowTour, TOUR_STEPS, tourSteps } from "../lib/tour";
import khTexts from "../../lang/en-US.json";
import khTextsDe from "../../lang/de-DE.json";

const open = { mustChangePassword: false, needsEmail: false, pendingEmail: null, tour: true, newsSeen: null };

describe("tourSteps", () => {
  test("has the eight steps in order", () => {
    expect(tourSteps(DEFAULT_ADDONS).map(step => step.key)).toEqual(
      ["welcome", "recipes", "intake", "shopping", "cook", "share", "phone", "more"],
    );
  });

  test("leaves out the shopping list while its add-on is off", () => {
    const keys = tourSteps({ ...DEFAULT_ADDONS, shopping: false }).map(step => step.key);
    expect(keys).toEqual(["welcome", "recipes", "intake", "cook", "share", "phone", "more"]);
  });
});

test("only the phone step has a button, and it leads to the setup page", () => {
  expect(TOUR_STEPS.filter(step => step.action).map(step => [step.key, step.action])).toEqual([["phone", "setup"]]);
});

describe("shouldShowTour", () => {
  test("shows it when the admin asked for it and no other first step is open", () => {
    expect(shouldShowTour(open, true)).toBe(true);
  });

  test("waits for the own password and the e-mail address", () => {
    expect(shouldShowTour({ ...open, mustChangePassword: true }, true)).toBe(false);
    expect(shouldShowTour({ ...open, needsEmail: true }, true)).toBe(false);
  });

  test("stays away without the flag, and without a status", () => {
    expect(shouldShowTour({ ...open, tour: false }, true)).toBe(false);
    expect(shouldShowTour(null, true)).toBe(false);
  });

  test("needs somebody signed in", () => {
    expect(shouldShowTour(open, false)).toBe(false);
  });
});

test("every step has a title and a text in both languages", () => {
  for (const texts of [khTexts, khTextsDe]) {
    const steps = texts.kh.tour.steps as Record<string, { title: string; text: string }>;
    for (const step of TOUR_STEPS) {
      expect(steps[step.key]?.title, step.key).toBeTruthy();
      expect(steps[step.key]?.text, step.key).toBeTruthy();
    }
  }
});
