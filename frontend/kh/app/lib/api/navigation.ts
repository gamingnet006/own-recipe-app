// KH: the API of a person's own side menu (D58) as a Mealie API class; the type is written by hand
// (mealie/kh/navigation).
import { BaseAPI } from "~/lib/api/base/base-clients";

export interface KhNavigationSettings {
  /** Keys of the side-menu entries the person hid. */
  hidden: string[];
  /** Whether the simple view (D79) is on. */
  simple: boolean;
}

export class KhNavigationApi extends BaseAPI {
  /** The own hidden entries. */
  async get() {
    return await this.requests.get<KhNavigationSettings>("/api/kh/navigation");
  }

  /** Stores the own hidden entries; without SIMPLE the stored simple view switch stays. */
  async put(hidden: string[], simple?: boolean) {
    return await this.requests.put<KhNavigationSettings, { hidden: string[]; simple?: boolean }>(
      "/api/kh/navigation",
      { hidden, simple },
    );
  }

  /** The admin reads a person's simple view switch. */
  async getSimple(userId: string) {
    return await this.requests.get<{ simple: boolean }>(`/api/kh/admin/navigation/${userId}`);
  }

  /** The admin switches a person's simple view. */
  async putSimple(userId: string, simple: boolean) {
    return await this.requests.put<{ simple: boolean }, { simple: boolean }>(`/api/kh/admin/navigation/${userId}`, { simple });
  }
}
