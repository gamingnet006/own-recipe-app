// KH: the drafts and first-steps calls show their own error text, so they ask Mealie's axios plugin for no second toast.
import { expect, test, vi } from "vitest";
import { KhDraftsApi } from "../lib/api/drafts";
import { KhOnboardingApi } from "../lib/api/onboarding";

function fakeRequests() {
  const call = vi.fn(async () => ({ data: null, error: null, response: null }));
  return { call, requests: { get: call, post: call, put: call, patch: call, delete: call } };
}

test("approve and edit of a draft suppress the generic toast", async () => {
  const { call, requests } = fakeRequests();
  const api = new KhDraftsApi(requests as never);
  await api.approve("d1", true);
  await api.edit("d1", { name: "Neu" });
  for (const args of call.mock.calls as unknown[][]) expect(args.at(-1)).toEqual({ suppressAlert: true });
});

test("first-steps calls suppress the generic toast", async () => {
  const { call, requests } = fakeRequests();
  await new KhOnboardingApi(requests as never).setPassword("long-enough");
  expect((call.mock.calls[0] as unknown[]).at(-1)).toEqual({ suppressAlert: true });
});
