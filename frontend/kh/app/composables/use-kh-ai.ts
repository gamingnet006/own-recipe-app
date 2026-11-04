// KH: the AI list in the settings (D39): moving a provider, deciding whether the page shows the own group, the words
// for a provider's state, and loading and ordering the list.
import { useRequests } from "~/composables/api/api-client";
import { KhAiApi, type KhProviderState } from "../lib/api/ai";

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

/** The words for a provider's state, with the time its pause ends where it has one. */
export function statusLabel(state: KhProviderState, t: Translate, time: (d: Date) => string): string {
  const until = state.pausedUntil ? time(new Date(state.pausedUntil)) : "";
  if (state.status === "quota" || state.status === "unreachable") {
    return t(`kh.ai.status.${state.status}`, { time: until });
  }
  return t(`kh.ai.status.${["key", "model"].includes(state.status) ? state.status : "ready"}`);
}

/** The group's list: loads it, and moves a provider up or down, saving the new order. */
export function useKhAiProviders() {
  const api = useKhAiApi();
  const providers = ref<KhProviderState[]>([]);

  async function load() {
    const { data } = await api.providers();
    providers.value = data ?? [];
  }

  async function move(index: number, delta: -1 | 1) {
    const ids = moveProvider(providers.value.map(p => p.providerId), index, delta);
    const { data } = await api.setOrder(ids);
    if (data) providers.value = data;
  }

  return { providers, load, move };
}
