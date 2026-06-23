<script setup lang="ts">
defineProps<{
  message: string;
}>();

defineEmits<{
  dismiss: [];
}>();
</script>

<template>
  <div v-if="message" class="error-banner" role="alert">
    <div>
      <strong>请求失败。</strong>
      <p>{{ message }}</p>
    </div>

    <button type="button" class="ghost-button" @click="$emit('dismiss')">
      关闭
    </button>
  </div>
</template>
