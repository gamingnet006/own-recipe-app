// KH: a "for this week" meal plan entry spans the same Monday-to-Sunday week as the planner shows (D76).
import { describe, expect, test, vi } from "vitest";
import { ref } from "vue";
import { useMealPlanEntryDates } from "~/composables/use-group-mealplan";

vi.mock("~/composables/api", () => ({ useUserApi: () => ({}) }));
vi.mock("~/composables/use-households", () => ({
  useHouseholdSelf: () => ({ household: ref({ preferences: { firstDayOfWeek: 0 } }) }),
}));
vi.mock("vue-i18n", async importOriginal => ({ ...await importOriginal<object>(), useI18n: () => ({ locale: ref("de-DE") }) }));

describe("useMealPlanEntryDates", () => {
  test("a week entry made from a Monday row runs Monday to Sunday for a German household", () => {
    const { selectedDate, isWeekEntry, entryDatesPayload } = useMealPlanEntryDates();
    selectedDate.value = new Date(2026, 10, 23); // Monday
    isWeekEntry.value = true;
    expect(entryDatesPayload.value).toEqual({ date: "2026-11-23", endDate: "2026-11-29" });
  });
});
