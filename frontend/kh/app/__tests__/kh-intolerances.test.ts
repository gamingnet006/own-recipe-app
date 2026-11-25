// KH: the question "Verträgst du etwas nicht?" (once per account) and the helper it shares with the profile page.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, test, vi } from "vitest";
import KhAllergenChoices from "../components/KhAllergenChoices.vue";
import KhIntolerancesDialog from "../components/KhIntolerancesDialog.vue";
import { toggleAllergen } from "../lib/api/allergens";
import { khOnboarding } from "../composables/use-kh-onboarding";
import { i18n } from "~/tests/setup";

const getMock = vi.hoisted(() => vi.fn());
const putMock = vi.hoisted(() => vi.fn());
const postMock = vi.hoisted(() => vi.fn());
vi.mock("~/composables/api/api-client", () => ({ useRequests: () => ({ get: getMock, put: putMock, post: postMock }) }));

// Vuetify is not installed in the tests: plain elements stand in for what the dialog uses
const stubs = {
  VDialog: { template: "<div><slot /></div>" },
  VBtn: { template: "<button><slot /></button>" },
  VCheckbox: {
    props: ["modelValue"],
    emits: ["update:modelValue"],
    template: "<input type=\"checkbox\" :checked=\"modelValue\" @change=\"$emit('update:modelValue', $event.target.checked)\">",
  },
};

describe("toggleAllergen", () => {
  test("ticks and unticks in the app's order, without duplicates", () => {
    expect(toggleAllergen(["milk"], "gluten", true)).toEqual(["gluten", "milk"]);
    expect(toggleAllergen(["gluten", "milk"], "gluten", false)).toEqual(["milk"]);
    expect(toggleAllergen(["milk"], "milk", true)).toEqual(["milk"]);
  });
});

describe("the question dialog", () => {
  beforeEach(() => {
    getMock.mockReset();
    putMock.mockReset();
    postMock.mockReset();
    getMock.mockResolvedValue({ data: { allergens: ["milk"] } });
    putMock.mockResolvedValue({ data: { allergens: ["gluten", "milk"] } });
    postMock.mockResolvedValue({ error: null });
    khOnboarding.status = { mustChangePassword: false, needsEmail: false, pendingEmail: null, tour: false, newsSeen: null, intolerancesAsked: false };
  });

  function open() {
    return mount(KhIntolerancesDialog, {
      props: { modelValue: true },
      global: { plugins: [i18n], components: { KhAllergenChoices }, stubs },
    });
  }

  test("saving stores the choice and marks the person as asked", async () => {
    const wrapper = open();
    await flushPromises();
    await wrapper.find("input[data-testid=\"intolerance-gluten\"], [data-testid=\"intolerance-gluten\"] input").setValue(true);
    await wrapper.find("[data-testid=\"intolerances-save\"]").trigger("click");
    await flushPromises();
    expect(putMock).toHaveBeenCalledWith("/api/kh/users/self/allergies", { allergens: ["gluten", "milk"] });
    expect(postMock).toHaveBeenCalledWith("/api/kh/onboarding/intolerances-asked", {}, expect.anything());
    expect(khOnboarding.status?.intolerancesAsked).toBe(true);
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([false]);
  });

  test("skipping only marks the person as asked", async () => {
    const wrapper = open();
    await flushPromises();
    await wrapper.find("[data-testid=\"intolerances-skip\"]").trigger("click");
    await flushPromises();
    expect(putMock).not.toHaveBeenCalled();
    expect(postMock).toHaveBeenCalledWith("/api/kh/onboarding/intolerances-asked", {}, expect.anything());
    expect(khOnboarding.status?.intolerancesAsked).toBe(true);
  });
});
