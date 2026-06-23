<script setup lang="ts">
import type { GenerationPhase } from "../types/chat";

const props = defineProps<{
  draft: string;
  generationLabel: string;
  generationPhase: GenerationPhase;
  isGenerating: boolean;
  canRetry: boolean;
}>();

const emit = defineEmits<{
  "update:draft": [value: string];
  submit: [];
  stop: [];
  retry: [];
}>();

// 保留常见聊天输入习惯：Enter 发送，Shift + Enter 换行。
function handleKeyDown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    emit("submit");
  }
}
</script>

<template>
  <div class="composer-shell">
    <label class="composer-label" for="chat-draft">
      输入内容
    </label>

    <div class="composer-row">
      <div class="composer-input-shell">
        <textarea
          id="chat-draft"
          class="composer-input"
          :value="props.draft"
          :disabled="props.isGenerating"
          placeholder="先描述你下一步想继续搭什么，我再接着和你一起推进。"
          rows="4"
          @input="emit('update:draft', ($event.target as HTMLTextAreaElement).value)"
          @keydown="handleKeyDown"
        />
        <p v-if="props.isGenerating" class="composer-hint">
          {{ props.generationLabel }}
        </p>
        <p v-else class="composer-hint">
          `Enter` 发送，`Shift + Enter` 换行
        </p>
      </div>

      <button
        type="button"
        :class="['primary-button', { danger: props.generationPhase === 'stopping' }]"
        @click="props.isGenerating ? emit('stop') : emit('submit')"
      >
        {{
          props.isGenerating
            ? props.generationPhase === "stopping"
              ? "停止中..."
              : "停止生成"
            : "发送"
        }}
      </button>

      <button
        v-if="props.canRetry && !props.isGenerating"
        type="button"
        class="secondary-button retry-button"
        @click="emit('retry')"
      >
        重试
      </button>
    </div>
  </div>
</template>
