// KH: the AI list in the settings (D39): moving a provider, deciding whether the page shows the own group, the words
// for a provider's state, loading and ordering the list, and the intake's hint about the AI.
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";
import { KhAiApi, type KhAiStatus, type KhProviderState } from "../lib/api/ai";

type Translate = (key: string, values?: Record<string, string>) => string;

/** Mealie's API requests with the AI list's routes. */
export function useKhAiApi(): KhAiApi {
  return new KhAiApi(useRequests());
}

/** A time of day as the reader's clock shows it, e.g. 9:00; for a pause's end and the bell. */
export function clockTime(date: Date, locale: string): string {
  return date.toLocaleTimeString(locale, { hour: "numeric", minute: "2-digit" });
}

/** The ids with the one at INDEX moved one place up (-1) or down (+1); at either end nothing moves. */
export function moveProvider(ids: string[], index: number, delta: -1 | 1): string[] {
  const target = index + delta;
  if (target < 0 || target >= ids.length) return ids;
  const moved = [...ids];
  [moved[index], moved[target]] = [moved[target]!, moved[index]!];
  return moved;
}

/** Whether Mealie's settings page shows the user's own group: its providers are exactly the list's. Mealie's
 * settings do not name their group, and admins can open other groups there too. */
export function sameProviders(khIds: string[], mealieIds: string[]): boolean {
  return khIds.length === mealieIds.length && khIds.every(id => mealieIds.includes(id));
}

/** The state the list shows at NOW: a pause that is over reads as ready, since the list asks that provider again. */
export function shownStatus(state: KhProviderState, now: Date): string {
  const over = state.pausedUntil !== null && new Date(state.pausedUntil) <= now;
  return (state.status === "quota" || state.status === "unreachable") && over ? "ready" : state.status;
}

/** The words for a provider's state at NOW, with the time its pause ends where it has one. */
export function statusLabel(state: KhProviderState, t: Translate, time: (d: Date) => string, now = new Date()): string {
  const status = shownStatus(state, now);
  const until = state.pausedUntil ? time(new Date(state.pausedUntil)) : "";
  if (status === "quota" || status === "unreachable") {
    return t(`kh.ai.status.${status}`, { time: until });
  }
  return t(`kh.ai.status.${["key", "model"].includes(status) ? status : "ready"}`);
}

/** Saves the new order and returns the list; when that fails, e.g. after another tab changed the providers, calls
 * FAIL and returns the list loaded anew. */
export async function saveOrder(
  api: Pick<KhAiApi, "setOrder" | "providers">,
  ids: string[],
  fail: () => void,
): Promise<KhProviderState[]> {
  const { data } = await api.setOrder(ids);
  if (data) return data;
  fail();
  return (await api.providers()).data ?? [];
}

/** Tells the settings Mealie's page loads anew from the editor's own changes passed up to the page (e.g. the audio
 * provider), so the list reloads once per load of the page's settings and not for every change. */
export function refreshWatch() {
  let passedUp: object | undefined;
  return {
    /** Hands VALUE up to the page and remembers it. */
    passUp<T extends object>(value: T): T {
      passedUp = value;
      return value;
    },
    /** Whether VALUE came from the page rather than from passUp. */
    isRefresh(value: object | null | undefined): boolean {
      return value != null && value !== passedUp;
    },
  };
}

/** The key of the intake's hint about the AI: none while one is available, else whether no provider is set up at all
 * or none can be reached now. */
export function aiHintKey(status: KhAiStatus | null | undefined): string | null {
  if (!status || status.available) return null;
  return status.configured ? "kh.ai.unavailable-hint" : "kh.ai.missing-hint";
}

/** The group's list: loads it, and moves a provider up or down, saving the new order. */
export function useKhAiProviders() {
  const api = useKhAiApi();
  const i18n = useI18n();
  const providers = ref<KhProviderState[]>([]);

  async function load() {
    const { data } = await api.providers();
    providers.value = data ?? [];
  }

  async function move(index: number, delta: -1 | 1) {
    const ids = moveProvider(providers.value.map(p => p.providerId), index, delta);
    providers.value = await saveOrder(api, ids, () => alert.error(i18n.t("kh.ai.order-failed")));
  }

  return { providers, load, move };
}
