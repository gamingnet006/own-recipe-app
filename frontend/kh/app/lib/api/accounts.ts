// KH: the API of switching households (D52) as a Mealie API class; the types are written by hand like the add-ons'
// (mealie/kh/accounts).
import { BaseAPI } from "~/lib/api/base/base-clients";

export interface KhAccount {
  userId: string;
  fullName: string;
  householdId: string;
  household: string;
  group: string;
  groupSlug: string;
  current: boolean;
}

export interface KhPerson {
  userId: string;
  fullName: string;
  accounts: KhAccount[];
}

export class KhAccountsApi extends BaseAPI {
  /** The person's accounts with the current one marked; empty without linked accounts. */
  async get() {
    return await this.requests.get<KhAccount[]>("/api/kh/accounts");
  }

  /** A session token for another account of the person. */
  async switch(userId: string) {
    return await this.requests.post<{ access_token: string; token_type: string }>("/api/kh/accounts/switch", { userId });
  }

  /** Admin: all persons with their accounts. */
  async people() {
    return await this.requests.get<KhPerson[]>("/api/kh/admin/accounts");
  }

  /** Admin: gives the person an account in the household. */
  async link(userId: string, householdId: string) {
    return await this.requests.post<KhAccount>("/api/kh/admin/accounts", { userId, householdId });
  }

  /** Admin: dissolves the link of a linked account; the account stays. */
  async unlink(userId: string) {
    return await this.requests.delete(`/api/kh/admin/accounts/${userId}`);
  }
}
