// KH: the API of a person's own side menu (D58) as a Mealie API class; the type is written by hand
// (mealie/kh/navigation).
import { BaseAPI } from "~/lib/api/base/base-clients";
import type { KhLocale } from "../locale";

export interface KhNavigationSettings {
  /** Keys of the side-menu entries the person hid. */
  hidden: string[];
  /** Whether the simple view (D79) is on. */
  simple: boolean;
  /** The language the person chose; null: they never did, the device decides. */
  locale: KhLocale | null;
}

export class KhNavigationApi extends BaseAPI {
  /** The own hidden entries. */
  async get() {
    return await this.requests.get<KhNavigationSettings>("/api/kh/navigation");
  }

  /** Stores the own hidden entries; without SIMPLE or LOCALE the stored switch and language stay. */
  async put(hidden: string[], simple?: boolean, locale?: KhLocale) {
    return await this.requests.put<KhNavigationSettings, { hidden: string[]; simple?: boolean; locale?: KhLocale }>(
      "/api/kh/navigation",
      { hidden, simple, locale },
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
