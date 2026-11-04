// KH: the AI list's API (D39) as a Mealie API class: the providers' order and state for managers, and whether any
// AI is available for everyone. The types are written by hand like the drafts' (mealie/kh/ai/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

const ai = "/api/kh/ai";

/** A provider with its place in the list and its state: ready, quota, key, model or unreachable. */
export interface KhProviderState {
  providerId: string;
  name: string;
  model: string;
  position: number;
  status: string;
  pausedUntil: string | null;
  supportsImages: boolean | null;
}

export interface KhAiStatus {
  available: boolean;
}

export class KhAiApi extends BaseAPI {
  /** The group's providers in the list's order. */
  async providers() {
    return await this.requests.get<KhProviderState[]>(`${ai}/providers`);
  }

  /** Sets the order; IDS names every provider of the group exactly once. */
  async setOrder(ids: string[]) {
    return await this.requests.put<KhProviderState[], { providerIds: string[] }>(`${ai}/providers/order`, {
      providerIds: ids,
    });
  }

  /** Whether any provider can take a request now. */
  async status() {
    return await this.requests.get<KhAiStatus>(`${ai}/status`);
  }
}
