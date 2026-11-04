<template>
  <!-- KH: the bell in the header for whoever manages the AI providers (D39): the number of unread notices, and
       opening it lists them, newest first -->
  <v-menu location="bottom end" :close-on-content-click="false" @update:model-value="(shown) => shown && open()">
    <template #activator="{ props: activator }">
      <v-btn v-bind="activator" icon :aria-label="$t('kh.notices.open')">
        <v-badge :model-value="unread > 0" :content="unread" color="error">
          <v-icon>{{ $globals.icons.bellOutline }}</v-icon>
        </v-badge>
      </v-btn>
    </template>
    <v-card min-width="280" max-width="360">
      <v-card-title class="text-title-medium">
        {{ $t("kh.notices.title") }}
      </v-card-title>
      <v-list v-if="items.length" density="compact" class="py-0">
        <v-list-item v-for="notice in items" :key="notice.id">
          <div class="text-body-medium">
            {{ noticeText(notice, translate, time) }}
          </div>
          <div class="text-body-small text-medium-emphasis">
            {{ when(notice.createdAt) }}
          </div>
        </v-list-item>
      </v-list>
      <v-card-text v-else>
        {{ $t("kh.notices.empty") }}
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
import { clockTime } from "../composables/use-kh-ai";
import { noticeText, useKhNotices } from "../composables/use-kh-notices";

const i18n = useI18n();
const { items, unread, open } = useKhNotices();

function translate(key: string, values?: Record<string, string>): string {
  return i18n.t(key, values ?? {});
}

/** A pause's end as the reader's clock shows it. */
function time(date: Date): string {
  return clockTime(date, i18n.locale.value);
}

/** When the notice came, as day and time. */
function when(createdAt: string): string {
  return new Date(createdAt).toLocaleString(i18n.locale.value, { dateStyle: "short", timeStyle: "short" });
}
</script>
