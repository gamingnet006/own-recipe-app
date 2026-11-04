<template>
  <div v-if="providerSettings">
    <BaseCardSectionTitle v-if="!hideHeader" :title="$t('group.ai-provider-settings.ai-provider-settings')">
      <template v-if="noDefaultProviderWarning" #append-title>
        <v-tooltip location="bottom" color="warning">
          <template #activator="{ props: tooltipProps }">
            <v-icon v-bind="tooltipProps" size="small" color="warning" class="ms-2">
              {{ $globals.icons.alert }}
            </v-icon>
          </template>
          <span>{{ $t('group.ai-provider-settings.no-default-provider-warning') }}</span>
        </v-tooltip>
      </template>
    </BaseCardSectionTitle>
    <v-card-text v-if="!hideHeader" class="pt-0 pb-10 px-0">
      {{ $t("group.ai-provider-settings.ai-provider-settings-description") }}
    </v-card-text>

    <v-row class="mb-4">
      <!-- KH: the priority list picks the default and the image provider in every group, also when an admin opens
           another group here; Mealie's two selects for them are gone (D39) -->
      <v-col cols="12">
        <v-autocomplete
          v-model="local.audioProviderId"
          :label="$t('group.ai-provider-settings.audio-provider')"
          :items="local.providers"
          item-title="name"
          item-value="id"
          clearable
          hide-details
          density="compact"
          variant="outlined"
        />
        <v-card-subtitle class="mt-1">
          {{ $t("group.ai-provider-settings.audio-provider-description") }}
        </v-card-subtitle>
      </v-col>
    </v-row>

    <GroupAIProviderDialog
      v-model="dialogOpen"
      :provider-id="editingProviderId ?? undefined"
      @create="(data) => $emit('create', data)"
      @update="(id, data) => $emit('update', id, data)"
    />

    <BaseCardSectionTitle
      :title="$t('group.ai-provider-settings.providers')"
      size="medium"
      class="pt-2"
    >
      <template #append-title>
        <BaseButton
          :text="$t('group.ai-provider-settings.create-provider')"
          class="ms-auto my-2"
          create
          small
          @click="openCreate"
        />
      </template>
    </BaseCardSectionTitle>

    <!-- KH: the own group gets the priority list with order and state, other groups keep Mealie's cards (D39) -->
    <KhAiProviderOrder
      v-if="khList"
      :providers="khProviders"
      @move="moveKhProvider"
      @edit="openEdit"
      @delete="(id) => $emit('delete', id)"
    />
    <v-card
      v-for="provider in local.providers"
      v-else
      :key="provider.id"
      variant="tonal"
      class="pa-0 mb-4"
    >
      <v-row no-gutters>
        <v-col :cols="10">
          <v-card-text>
            {{ provider.name }}
          </v-card-text>
        </v-col>

        <v-col :cols="2">
          <BaseButtonGroup
            :buttons="[
              {
                icon: $globals.icons.edit,
                text: $t('general.edit'),
                event: 'edit',
              },
              {
                icon: $globals.icons.delete,
                text: $t('general.delete'),
                event: 'delete',
              },
            ]"
            @edit="openEdit(provider.id)"
            @delete="$emit('delete', provider.id)"
          />
        </v-col>
      </v-row>
    </v-card>

    <!-- KH: where free AI keys come from (D39) -->
    <KhFreeAiKeys />
  </div>
</template>

<script setup lang="ts">
import type { AIProviderCreate, AIProviderUpdate } from "~/lib/api/types/group";
import type { AIProviderSettingsOut } from "~/lib/api/types/user";

const providerSettings = defineModel<AIProviderSettingsOut>({ required: true });

const props = withDefaults(defineProps<{
  hideHeader?: boolean;
}>(), {
  hideHeader: false,
});

const { hideHeader } = toRefs(props);

const local = reactive({ ...providerSettings.value });
const khRefresh = refreshWatch(); // KH: tells the page's loads from this editor's own changes (D39)
watch(local, (newVal) => { providerSettings.value = khRefresh.passUp({ ...newVal }); });
// Sync back when the parent refreshes after create/update/delete
watch(providerSettings, (newVal) => { if (newVal) Object.assign(local, newVal); });

const noDefaultProviderWarning = computed(
  () => local.providers.length > 0 && !local.defaultProviderId,
);

// KH: the own group's priority list (D39), reloaded whenever the page loads the settings anew, not for this editor's
// own changes; shown only when its providers are the page's, since admins may open other groups here too
const { providers: khProviders, load: loadKhProviders, move: moveKhProvider } = useKhAiProviders();
const khList = computed(() => sameProviders(khProviders.value.map(p => p.providerId), local.providers.map(p => p.id)));
watch(providerSettings, (settings) => { if (khRefresh.isRefresh(settings)) loadKhProviders(); }, { immediate: true });

defineEmits<{
  (e: "create", data: AIProviderCreate): void;
  (e: "update", id: string, data: AIProviderUpdate): void;
  (e: "delete", id: string): void;
}>();

const dialogOpen = ref(false);
const editingProviderId = ref<string | null>(null);

function openCreate() {
  editingProviderId.value = null;
  dialogOpen.value = true;
}

function openEdit(id: string) {
  editingProviderId.value = id;
  dialogOpen.value = true;
}
</script>
