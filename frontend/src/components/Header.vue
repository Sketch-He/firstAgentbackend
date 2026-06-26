<script setup lang="ts">
import type { ServiceStatus } from "../composables/useServiceHealth";
import type { GenerationPhase } from "../types/chat";

defineProps<{
  generationLabel: string;
  generationPhase: GenerationPhase;
  isGenerating: boolean;
  modelName: string;
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
    <!-- <div> -->
      <!-- <p class="eyebrow">Agent Demo</p> -->
      <!-- <h1>先搭聊天壳，再演进 Agent。</h1> -->
      <!-- <p class="shell-copy"> -->
        <!-- 当前普通对话和 SSE 流式输出都已接通真实模型调用，下一步继续补强消息体验和工具能力。 -->
      <!-- </p> -->
    <!-- </div> -->

    <div class="header-actions">
      <!-- <button
        type="button"
        class="ghost-button"
        @click="$emit('retryHealth')"
      >
        {{ serviceStatus === "checking" ? "检查中..." : `${serviceName}：${serviceStatus === "online" ? "在线" : "离线"}` }}
      </button>
      <span :class="['status-pill', { live: isGenerating, stopping: generationPhase === 'stopping' }]">
        {{ isGenerating ? generationLabel : "交互完善中" }}
      </span>
      <span v-if="modelName" class="model-pill">{{ modelName }}</span>
      <button type="button" class="secondary-button" @click="$emit('reset')">
        新对话
      </button> -->
    </div>
  </header>
</template>
