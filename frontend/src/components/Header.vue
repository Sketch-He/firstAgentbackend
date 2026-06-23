<script setup lang="ts">
import type { ServiceStatus } from "../composables/useServiceHealth";

defineProps<{
  isGenerating: boolean;
  serviceName: string;
  serviceStatus: ServiceStatus;
}>();

defineEmits<{
  reset: [];
  retryHealth: [];
}>();
</script>

<template>
  <header class="shell-header">
    <div>
      <p class="eyebrow">Agent Demo</p>
      <h1>先搭聊天壳，再演进 Agent。</h1>
      <p class="shell-copy">
        当前普通对话已经接通真实模型调用，下一步可以继续接流式输出和工具能力。
      </p>
    </div>

    <div class="header-actions">
      <button
        type="button"
        class="ghost-button"
        @click="$emit('retryHealth')"
      >
        {{ serviceStatus === "checking" ? "检查中..." : `${serviceName}：${serviceStatus === "online" ? "在线" : "离线"}` }}
      </button>
      <span :class="['status-pill', { live: isGenerating }]">
        {{ isGenerating ? "生成中" : "骨架阶段" }}
      </span>
      <button type="button" class="secondary-button" @click="$emit('reset')">
        新对话
      </button>
    </div>
  </header>
</template>
