// KH: the bell's API (D39) as a Mealie API class; the types are written by hand like the drafts'
// (mealie/kh/notices/schemas.py).
import { BaseAPI } from "~/lib/api/base/base-clients";

const notices = "/api/kh/notices";

/** One notice as kind and values; the frontend words it in the reader's language. */
export interface KhNotice {
  id: string;
  kind: string;
  provider: string | null;
  nextProvider: string | null;
  until: string | null;
  createdAt: string;
}

export interface KhNotices {
  items: KhNotice[];
  unread: number;
}

export class KhNoticesApi extends BaseAPI {
  /** The group's newest notices, newest first, and how many are unread. */
  async list() {
    return await this.requests.get<KhNotices>(notices);
  }

  /** Marks every notice so far as read. */
  async read() {
    return await this.requests.post<undefined, undefined>(`${notices}/read`, undefined);
  }
}
