<!-- KH: asked when the admin leaves the setup's "Familie" step with people typed in but not created (D83): create them
now or throw them away. -->
<template>
  <v-dialog v-model="open" max-width="420">
    <v-card>
      <v-card-title class="text-wrap">
        {{ $t("kh.wizard.family.pending-title", count) }}
      </v-card-title>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="discard">
          {{ $t("kh.wizard.family.discard") }}
        </v-btn>
        <v-btn color="primary" variant="flat" :disabled="!canCreate" :loading="busy" @click="createNow">
          {{ $t("kh.wizard.family.create-now") }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { discardRows, pendingCount, useKhSetupFamily } from "../composables/use-kh-setup-family";

const open = defineModel<boolean>({ required: true });
const emit = defineEmits<{ next: [] }>();

const { canCreate, create } = useKhSetupFamily();
const busy = ref(false);
const count = computed(() => pendingCount());

/** Creates the people; the wizard goes on only when all of them exist, else the rows show what went wrong. */
async function createNow() {
  busy.value = true;
  const allCreated = await create();
  busy.value = false;
  open.value = false;
  if (allCreated) emit("next");
}

function discard() {
  discardRows();
  open.value = false;
  emit("next");
}
</script>
