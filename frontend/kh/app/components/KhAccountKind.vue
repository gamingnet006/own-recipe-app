<!-- KH: the kind of an account (Familie, Verwaltung, Admin) instead of six checkboxes; the single flags stay under "Einzeln
einstellen". An account with another mix shows "Eigene Auswahl". Used where an admin creates or edits a person. -->
<template>
  <div class="my-2">
    <h3 class="text-subtitle-1 font-weight-bold">
      {{ $t("kh.kind.title") }}
    </h3>
    <v-radio-group
      :model-value="kind"
      color="primary"
      hide-details
      :aria-label="$t('kh.kind.title')"
      @update:model-value="choose($event as KhAccountKind)"
    >
      <v-radio
        v-for="value in ACCOUNT_KINDS"
        :key="value"
        :value="value"
        :disabled="value === 'admin' && disableAdmin"
        :label="kindLabel(value)"
      />
      <v-radio v-if="kind === 'custom'" value="custom" disabled :label="$t('kh.kind.custom')" />
    </v-radio-group>
    <v-expansion-panels v-if="!kindOnly" variant="accordion" class="mt-2">
      <v-expansion-panel :title="$t('kh.kind.individual')">
        <v-expansion-panel-text>
          <v-checkbox
            v-for="key in FLAG_KEYS"
            :key="key"
            :model-value="flags[key]"
            :label="$t(FLAG_LABELS[key])"
            :disabled="key === 'admin' && disableAdmin"
            color="primary"
            density="compact"
            hide-details
            @update:model-value="emit('update:flags', applyFlag(flags, key, !!$event))"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup lang="ts">
import {
  ACCOUNT_KINDS, applyFlag, FLAG_KEYS, flagsOfKind, kindOfFlags, type KhAccountFlags, type KhAccountKind, type KhFlagKey,
} from "../lib/account-kind";

const props = defineProps<{
  /** The person (or the new person's data): the six flags are read from it. */
  flags: KhAccountFlags;
  /** Admin can only be given to accounts that sign in with Mealie's own password. */
  disableAdmin?: boolean;
  /** Only the three kinds, without the single checkboxes (the setup wizard). */
  kindOnly?: boolean;
}>();
const emit = defineEmits<{ "update:flags": [flags: KhAccountFlags] }>();

// Mealie's own texts for the six flags
const FLAG_LABELS: Record<KhFlagKey, string> = {
  admin: "user.administrator",
  advanced: "user.enable-advanced-features",
  canInvite: "user.user-can-invite-other-to-group",
  canManage: "user.user-can-manage-group",
  canManageHousehold: "user.user-can-manage-household",
  canOrganize: "user.user-can-organize-group-data",
};

const { t } = useI18n();

/** "Familie · daily use ...": the name and what the kind can do. */
function kindLabel(value: KhAccountKind): string {
  return `${t(`kh.kind.${value}`)} · ${t(`kh.kind.${value}-hint`)}`;
}

const kind = computed(() => kindOfFlags(props.flags));

function choose(value: KhAccountKind) {
  emit("update:flags", flagsOfKind(value));
}
</script>
