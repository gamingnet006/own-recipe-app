// KH: tests for the cook-mode position (D42): Next and Back within the bounds, the step in the address, and recipes
// with no or one step.
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { reactive } from "vue";
import { useKhCook } from "../composables/use-kh-cook";

const query = reactive<Record<string, string>>({});

beforeEach(() => {
  delete query.step;
  vi.stubGlobal("useRoute", () => ({ query }));
  vi.stubGlobal("useRouter", () => ({ replace: (to: { query: Record<string, string> }) => Object.assign(query, to.query) }));
});

describe("useKhCook", () => {
  test("next and back stay within the steps", () => {
    const cook = useKhCook(() => 3);
    cook.back();
    expect(cook.step.value).toBe(0);
    cook.next();
    cook.next();
    cook.next();
    expect(cook.step.value).toBe(2);
    cook.back();
    expect(cook.step.value).toBe(1);
  });

  test("goTo clamps", () => {
    const cook = useKhCook(() => 3);
    cook.goTo(99);
    expect(cook.step.value).toBe(2);
    cook.goTo(-4);
    expect(cook.step.value).toBe(0);
  });

  test("one step is the first and the last; no steps do not crash", () => {
    const one = useKhCook(() => 1);
    expect(one.isFirst.value && one.isLast.value).toBe(true);
    one.next();
    expect(one.step.value).toBe(0);
    const none = useKhCook(() => 0);
    none.next();
    none.goTo(5);
    expect(none.step.value).toBe(0);
  });

  test("starts at the step in the address, 1-based; nonsense gives the first", () => {
    query.step = "3";
    expect(useKhCook(() => 5).step.value).toBe(2);
    query.step = "abc";
    expect(useKhCook(() => 5).step.value).toBe(0);
    query.step = "9";
    expect(useKhCook(() => 5).step.value).toBe(4);
  });

  test("writes the step into the address", async () => {
    const cook = useKhCook(() => 5);
    cook.goTo(3);
    await flushPromises();
    expect(query.step).toBe("4");
  });

  test("all steps is off at first", () => {
    expect(useKhCook(() => 2).allSteps.value).toBe(false);
  });
});
