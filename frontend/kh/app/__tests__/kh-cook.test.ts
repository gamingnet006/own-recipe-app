// KH: tests for the cook-mode position (D42): Next and Back within the bounds, the step in the address, and recipes
// with no or one step.
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { reactive, ref } from "vue";
import { cookForward, handleCookKey, showsSegments, useKhCook } from "../composables/use-kh-cook";

const query = reactive<Record<string, string>>({});

beforeEach(() => {
  delete query.step;
  delete query.cook;
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

  test("finishing drops cook and step from the address in one write", () => {
    query.step = "5";
    query.cook = "true";
    useKhCook(() => 5).finish();
    expect(query.step).toBeUndefined();
    expect(query.cook).toBeUndefined();
  });

  test("all steps is off at first", () => {
    expect(useKhCook(() => 2).allSteps.value).toBe(false);
  });

  test("all steps is off again when cook mode is opened anew", async () => {
    const open = ref(true);
    const cook = useKhCook(() => 2, () => open.value);
    cook.allSteps.value = true;
    open.value = false;
    await flushPromises();
    open.value = true;
    await flushPromises();
    expect(cook.allSteps.value).toBe(false);
  });
});

test("opening cook mode again after the last step starts at the first (v1.3)", async () => {
  const open = ref(true);
  const cook = useKhCook(() => 4, () => open.value);
  cook.goTo(3);
  open.value = false;
  await flushPromises();
  open.value = true;
  await flushPromises();
  expect(cook.step.value).toBe(0);
  expect(query.step).toBe("4"); // the restart is not written, so it cannot race the opening in the address
  cook.next();
  await flushPromises();
  expect(query.step).toBe("2"); // the next move writes again
});

test("opening cook mode again in the middle stays at that step", async () => {
  const open = ref(true);
  const cook = useKhCook(() => 4, () => open.value);
  cook.goTo(2);
  open.value = false;
  await flushPromises();
  open.value = true;
  await flushPromises();
  expect(cook.step.value).toBe(2);
});

test("Fertig on the last step closes, and the next opening starts at the first step (v1.3)", async () => {
  const open = ref(true);
  const cook = useKhCook(() => 3, () => open.value);
  cook.goTo(2);
  cookForward(cook, () => (open.value = false));
  await flushPromises();
  expect(open.value).toBe(false);
  expect(query.step).toBe("3"); // closing writes no step, so it cannot race the closing in the address
  open.value = true;
  await flushPromises();
  expect(cook.step.value).toBe(0);
});

test("the progress bar is one continuous bar from 12 steps on", () => {
  expect(showsSegments(11)).toBe(true);
  expect(showsSegments(12)).toBe(false);
});

describe("cook keys", () => {
  const press = (key: string, target: HTMLElement = document.body, init: KeyboardEventInit = {}) => {
    const cook = useKhCook(() => 5);
    cook.goTo(2);
    const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...init });
    target.addEventListener("keydown", e => handleCookKey(cook, e), { once: true });
    target.dispatchEvent(event);
    return { step: cook.step.value, event };
  };

  test("arrows and the space bar move between steps", () => {
    expect(press("ArrowRight").step).toBe(3);
    expect(press("ArrowLeft").step).toBe(1);
    const space = press(" ");
    expect(space.step).toBe(3);
    expect(space.event.defaultPrevented).toBe(true);
  });

  test("keys with a modifier, in fields and on buttons keep their own job", () => {
    expect(press("ArrowRight", document.body, { ctrlKey: true }).step).toBe(2);
    const input = document.body.appendChild(document.createElement("input"));
    expect(press("ArrowRight", input).step).toBe(2);
    const button = document.body.appendChild(document.createElement("button"));
    const onButton = press(" ", button);
    expect(onButton.step).toBe(2);
    expect(onButton.event.defaultPrevented).toBe(false);
    expect(press("ArrowRight", button).step).toBe(3);
  });

  test("forward goes on, and on the last step it closes", () => {
    const close = vi.fn();
    const cook = useKhCook(() => 2);
    cookForward(cook, close);
    expect(cook.step.value).toBe(1);
    expect(close).not.toHaveBeenCalled();
    cookForward(cook, close);
    expect(close).toHaveBeenCalledTimes(1);
  });
});
