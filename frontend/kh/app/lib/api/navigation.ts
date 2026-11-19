// KH: the API of a person's own side menu (D58) as a Mealie API class; the type is written by hand
// (mealie/kh/navigation).
import { BaseAPI } from "~/lib/api/base/base-clients";

export interface KhNavigationSettings {
  /** Keys of the side-menu entries the person hid. */
  hidden: string[];
}

export class KhNavigationApi extends BaseAPI {
  /** The own hidden entries. */
  async get() {
    return await this.requests.get<KhNavigationSettings>("/api/kh/navigation");
  }

  /** Stores the own hidden entries. */
  async put(hidden: string[]) {
    return await this.requests.put<KhNavigationSettings, KhNavigationSettings>("/api/kh/navigation", { hidden });
  }
}
