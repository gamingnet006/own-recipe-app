// KH: switching households (D52) as one shared state: the person's accounts, and the switch itself. A switch sets the
// new token and reloads the app, which clears every list and state of the old household.
import { computed, reactive } from "vue";
import { type KhAccount, KhAccountsApi } from "../lib/api/accounts";
import { useRequests } from "~/composables/api/api-client";
import { useAuthBackend } from "~/composables/use-auth-backend";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";

export const khAccounts = reactive({ list: [] as KhAccount[] });

export function useKhAccounts() {
  const auth = useAuthBackend();

  /** Loads the person's accounts; stays empty (no switch shown) when the request fails. */
  async function load(): Promise<void> {
    const { data } = await new KhAccountsApi(useRequests()).get();
    khAccounts.list = data ?? [];
  }

  /** Signs in to the account, then reloads the target's group start page. */
  async function switchTo(userId: string): Promise<void> {
    const target = khAccounts.list.find(account => account.userId === userId);
    const { data } = await new KhAccountsApi(useRequests()).switch(userId);
    if (!data || !target) {
      alert.error(useGlobalI18n().t("events.something-went-wrong"));
      return;
    }
    auth.setToken(data.access_token);
    location.assign(`/g/${target.groupSlug}`);
  }

  return { accounts: computed(() => khAccounts.list), current: computed(() => khAccounts.list.find(a => a.current)), load, switchTo };
}
