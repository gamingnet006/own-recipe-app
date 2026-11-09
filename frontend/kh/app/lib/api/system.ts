// KH: the About page's, the auto-update checkbox's and the system check's API (P8) as a Mealie API class; the types are
// written by hand like the drafts' (mealie/kh/system/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

const about = "/api/kh/about";
const autoUpdate = "/api/kh/admin/auto-update";
const system = "/api/kh/admin/system";

export interface KhAbout {
  version: string;
  notices: string; // THIRD_PARTY_NOTICES.md, empty when the file is not in the image
}

export interface KhAutoUpdate {
  enabled: boolean | null; // null: no file yet, KH_AUTO_UPDATE in .env decides
  status: string | null; // the last run, null before the first one
}

export type KhLight = "ok" | "warn" | "bad" | "info";

export interface KhCheck {
  key: string;
  state: KhLight;
  value: string;
}

export class KhSystemApi extends BaseAPI {
  /** The running release and the third-party notices. */
  async about() {
    return await this.requests.get<KhAbout>(about);
  }

  /** The checkbox and the last run (admins). */
  async getAutoUpdate() {
    return await this.requests.get<KhAutoUpdate>(autoUpdate);
  }

  /** Sets the checkbox; auto_update.sh picks it up at the next run (admins). */
  async setAutoUpdate(enabled: boolean) {
    return await this.requests.put<KhAutoUpdate, { enabled: boolean }>(autoUpdate, { enabled });
  }

  /** One traffic light per row of the system check (admins). */
  async checks() {
    return await this.requests.get<KhCheck[]>(system);
  }
}
