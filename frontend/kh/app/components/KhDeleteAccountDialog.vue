<!-- KH: "Konto löschen" (D78): shows who inherits the recipes and lists, asks to type the username, deletes the
     account and signs out. The server refuses the last admin or the last person of a household and says why. -->
<template>
  <v-dialog v-model="open" max-width="520">
    <v-card :title="$t('kh.account-delete.title')">
      <v-card-text v-if="preview">
        <p v-if="preview.blocked" class="text-error">
          {{ preview.blocked }}
        </p>
        <template v-else>
          <p class="mb-4">
            {{ summary }}
          </p>
          <v-text-field
            v-model="typed"
            :label="$t('kh.account-delete.confirm-label')"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
            hide-details
          />
        </template>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="open = false">
          {{ $t("general.cancel") }}
        </v-btn>
        <v-btn
          v-if="preview && !preview.blocked"
          color="error"
          variant="flat"
          :disabled="!confirmMatches(typed, username)"
          :loading="busy"
          @click="remove"
        >
          {{ $t("kh.account-delete.entry") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { confirmMatches } from "../lib/account-delete";
import { type KhDeletePreview, KhAccountsApi } from "../lib/api/accounts";
import { useRequests } from "~/composables/api/api-client";
import { alert } from "~/composables/use-toast";

const open = defineModel<boolean>({ default: false });
const i18n = useI18n();
const auth = useMealieAuth();
const api = new KhAccountsApi(useRequests());

const preview = ref<KhDeletePreview | null>(null);
const typed = ref("");
const busy = ref(false);
const username = computed(() => auth.user.value?.username ?? "");

const summary = computed(() => {
  const found = preview.value;
  if (!found || !found.heir || found.recipes + found.lists === 0) {
    return i18n.t("kh.account-delete.nothing");
  }
  return i18n.t("kh.account-delete.keeps", {
    recipes: i18n.t("kh.account-delete.recipes", { count: found.recipes }, found.recipes),
    lists: i18n.t("kh.account-delete.lists", { count: found.lists }, found.lists),
    heir: found.heir.name,
  });
});

// Asks the server each time the dialog opens, so the numbers and the heir are current.
watch(open, async (isOpen) => {
  if (!isOpen) {
    return;
  }
  typed.value = "";
  preview.value = null;
  const { data } = await api.deletePreview();
  preview.value = data;
});

/** Deletes the account, signs out (no reload, so the toast stays) and shows the login page. */
async function remove() {
  busy.value = true;
  const { error } = await api.deleteOwn(typed.value);
  busy.value = false;
  if (error) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }
  open.value = false;
  await auth.signOut("/login?direct=1");
  alert.success(i18n.t("kh.account-delete.done"));
}
</script>
