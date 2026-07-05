<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";
import type { GenerationPhase, RagMode } from "../types/chat";

const props = defineProps<{
  draft: string;
  generationLabel: string;
  generationPhase: GenerationPhase;
  isGenerating: boolean;
  canRetry: boolean;
  ragMode: RagMode;
  hasDocuments: boolean;
}>();

const emit = defineEmits<{
  "update:draft": [value: string];
  submit: [];
  stop: [];
  retry: [];
  "update:ragMode": [value: RagMode];
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const minTextareaHeight = 136;
const maxTextareaHeight = minTextareaHeight * 2;

function resizeTextarea() {
  const textarea = textareaRef.value;

  if (!textarea) {
    return;
  }

  textarea.style.height = `${minTextareaHeight}px`;
  const nextHeight = Math.min(textarea.scrollHeight, maxTextareaHeight);
  textarea.style.height = `${Math.max(minTextareaHeight, nextHeight)}px`;
  textarea.style.overflowY = textarea.scrollHeight > maxTextareaHeight ? "auto" : "hidden";
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    emit("submit");
  }
}

function handleInput(event: Event) {
  emit("update:draft", (event.target as HTMLTextAreaElement).value);
}

onMounted(() => {
  resizeTextarea();
});

watch(
  () => props.draft,
  async () => {
    await nextTick();
    resizeTextarea();
  }
);
</script>

<template>
  <div class="composer-shell">
    <div class="composer-card">
      <div class="composer-input-block">
        <textarea
          id="chat-draft"
          ref="textareaRef"
          class="composer-input"
          :value="props.draft"
          :disabled="props.isGenerating"
          placeholder="发送消息"
          rows="5"
          @input="handleInput"
          @keydown="handleKeyDown"
        />
      </div>

      <div class="composer-toolbar">
        <div class="composer-tools">
          <button
            v-if="props.canRetry && !props.isGenerating"
            type="button"
            class="composer-chip"
            @click="emit('retry')"
          >
            重试
          </button>

          <div v-if="props.hasDocuments" class="rag-mode-group">
            <button
              v-for="mode in (['auto', 'always', 'never'] as RagMode[])"
              :key="mode"
              type="button"
              :class="['rag-mode-btn', { active: props.ragMode === mode }]"
              :title="mode === 'auto' ? '自动判断是否检索' : mode === 'always' ? '始终检索知识库' : '不使用知识库'"
              @click="emit('update:ragMode', mode)"
            >
              {{ mode === 'auto' ? '🤖' : mode === 'always' ? '📚' : '💬' }}
            </button>
          </div>

          <span class="composer-hint">
            {{ props.isGenerating ? props.generationLabel : "`Enter` 发送，`Shift + Enter` 换行" }}
          </span>
        </div>

        <button
          type="button"
          :class="['composer-send-button', { stopping: props.generationPhase === 'stopping' }]"
          :aria-label="props.isGenerating ? '停止生成' : '发送消息'"
          @click="props.isGenerating ? emit('stop') : emit('submit')"
        >
          <span v-if="props.isGenerating" class="composer-send-stop">■</span>
          <svg
            v-else
            class="composer-send-icon"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M12 18V6M12 6L7 11M12 6L17 11"
              stroke="currentColor"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
