<!-- KH: the admin's switch of the simple view for one person, on Mealie's user edit page (D79); it saves at once, so it
needs no "Update". -->
<template>
  <v-switch
    v-if="simple !== null"
    :model-value="simple"
    :label="$t('kh.simple.admin-label')"
    :hint="$t('kh.simple.text')"
    persistent-hint
    color="primary"
    class="mb-2"
    @update:model-value="change(!!$event)"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { KhNavigationApi } from "../lib/api/navigation";
import { useRequests } from "~/composables/api/api-client";

const props = defineProps<{ userId: string }>();

const simple = ref<boolean | null>(null); // hidden until known; a failed read leaves the switch out
const api = new KhNavigationApi(useRequests());

onMounted(async () => {
  simple.value = (await api.getSimple(props.userId)).data?.simple ?? null;
});

/** Stores the new value; the switch shows what the server answered, so a failure leaves it as it was. */
async function change(value: boolean) {
  const { data } = await api.putSimple(props.userId, value);
  if (data) simple.value = data.simple;
}
</script>
