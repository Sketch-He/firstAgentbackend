<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { GenerationPhase, RagSource } from "../types/chat";
import type { ChatMessage } from "../types/chat";
import MessageBubble from "./MessageBubble.vue";

const props = defineProps<{
  generationLabel: string;
  generationPhase: GenerationPhase;
  isGenerating: boolean;
  messages: ChatMessage[];
  messageSources?: Record<string, RagSource[]>;
}>();

const shouldAutoScroll = ref(true);

function getScrollRoot() {
  return document.scrollingElement ?? document.documentElement;
}

function scrollToBottom() {
  window.scrollTo({
    top: getScrollRoot().scrollHeight
  });
}

function handleWindowScroll() {
  const distanceToBottom =
    getScrollRoot().scrollHeight - (window.scrollY + window.innerHeight);

  shouldAutoScroll.value = distanceToBottom < 80;
}

onMounted(() => {
  window.addEventListener("scroll", handleWindowScroll, { passive: true });

  void nextTick().then(() => {
    if (shouldAutoScroll.value) {
      scrollToBottom();
    }
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleWindowScroll);
});

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
    <div class="message-list">
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :sources="messageSources?.[message.id]"
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
