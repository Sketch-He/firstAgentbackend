<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import type { GenerationPhase } from "../types/chat";
import type { ChatMessage } from "../types/chat";
import MessageBubble from "./MessageBubble.vue";

const props = defineProps<{
  generationLabel: string;
  generationPhase: GenerationPhase;
  isGenerating: boolean;
  messages: ChatMessage[];
}>();

const listRef = ref<HTMLElement | null>(null);
const shouldAutoScroll = ref(true);

function scrollToBottom() {
  const element = listRef.value;

  if (!element) {
    return;
  }

  element.scrollTop = element.scrollHeight;
}

function handleScroll() {
  const element = listRef.value;

  if (!element) {
    return;
  }

  const distanceToBottom =
    element.scrollHeight - element.scrollTop - element.clientHeight;

  shouldAutoScroll.value = distanceToBottom < 80;
}

watch(
  () => [
    props.messages.length,
    props.messages[props.messages.length - 1]?.content,
    props.isGenerating
  ],
  async () => {
    if (!shouldAutoScroll.value) {
      return;
    }

    await nextTick();
    scrollToBottom();
  }
);
</script>

<template>
  <section class="message-panel">
    <div ref="listRef" class="message-list" @scroll="handleScroll">
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />

      <div v-if="isGenerating" class="typing-row" aria-live="polite">
        <div class="typing-dots" :class="generationPhase">
          <span />
          <span />
          <span />
        </div>
        <p class="typing-copy">{{ generationLabel }}</p>
      </div>
    </div>
  </section>
</template>
