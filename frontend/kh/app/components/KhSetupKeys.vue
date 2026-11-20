<!-- KH: the keys made on the setup page (D86) as copy boxes, with the buttons to make the first and further ones and the
note that they are only visible now. The keys live in the page, nowhere else. -->
<template>
  <div>
    <v-btn
      v-if="!keys.length"
      :variant="primary ? 'elevated' : 'tonal'"
      color="primary"
      size="large"
      :loading="making"
      @click="$emit('make')"
    >
      {{ $t("kh.setup.key.create") }}
    </v-btn>
    <template v-else>
      <KhCopyField
        v-for="(key, i) in keys"
        :key="i"
        :label="i ? `${$t('kh.setup.key.label')} ${i + 1}` : $t('kh.setup.key.label')"
        :value="key"
        class="mb-2"
      />
      <v-alert type="warning" variant="tonal" density="compact" class="mt-2">
        {{ $t("kh.setup.key.once") }}
      </v-alert>
      <v-btn variant="text" :loading="making" class="mt-1" @click="$emit('make')">
        {{ $t("kh.setup.key.another") }}
      </v-btn>
      <p class="text-body-2 text-medium-emphasis">
        {{ $t("kh.setup.key.one-each") }}
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
defineProps<{ keys: string[]; making: boolean; primary?: boolean }>();
defineEmits<{ make: [] }>();
</script>
