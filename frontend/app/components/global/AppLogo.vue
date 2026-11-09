<template>
  <div class="icon-container">
    <v-divider class="icon-divider" />
    <v-avatar
      :class="['pa-2', 'icon-avatar']"
      color="#E6F2EC"
      :size="size"
    >
      <slot>
        <!-- KH: Kochheft's logo replaces Mealie's icon when no custom logo is set (D49) -->
        <v-img
          :src="$appInfo.brandingLogoUrl || '/icons/kochheft-logo.svg'"
          :width="size"
          :height="size"
        />
      </slot>
    </v-avatar>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 75 });
</script>

<style scoped>
.icon-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  position: relative;
  margin-top: 2.5rem;
}
.icon-divider {
  width: 100%;
  margin-bottom: -2.5rem;
}
.icon-avatar {
  border-color: rgba(0, 0, 0, 0.12);
  border: 2px;
}
</style>
