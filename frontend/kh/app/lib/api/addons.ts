// KH: the API of the add-ons page (D46) as a Mealie API class; the types are written by hand like the notices'
// (mealie/kh/addons).
import type { KhAddonFlags, KhAddonsAnswer } from "../addons";
import { BaseAPI } from "~/lib/api/base/base-clients";

export class KhAddonsApi extends BaseAPI {
  /** The household's switches; everyone may read them. */
  async get() {
    return await this.requests.get<KhAddonsAnswer>("/api/kh/addons");
  }

  /** Stores all switches (admins only). */
  async put(flags: KhAddonFlags) {
    return await this.requests.put<KhAddonsAnswer, KhAddonFlags>("/api/kh/addons", flags);
  }
}
