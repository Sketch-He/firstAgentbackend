<script setup lang="ts">
import Composer from "../components/Composer.vue";
import ErrorBanner from "../components/ErrorBanner.vue";
import Header from "../components/Header.vue";
import MessageList from "../components/MessageList.vue";
import { useChat } from "../composables/useChat";
import { useServiceHealth } from "../composables/useServiceHealth";

const {
  canRetry,
  draft,
  error,
  generationLabel,
  generationPhase,
  isGenerating,
  latestStreamMeta,
  messages,
  resetConversation,
  retryLastTurn,
  setDraft,
  setError,
  stopGeneration,
  submitDraft
} = useChat();

const { checkHealth, serviceName, status } = useServiceHealth();
</script>

<template>
  <!-- 目前页面只承载聊天主流程，后面再按需要拆侧边栏、设置区和工具区。 -->
  <main class="app-shell">
    <div class="glow glow-left" />
    <div class="glow glow-right" />

    <section class="chat-shell">
      <Header
        :generation-label="generationLabel"
        :generation-phase="generationPhase"
        :is-generating="isGenerating"
        :model-name="latestStreamMeta?.model ?? ''"
        :service-name="serviceName"
        :service-status="status"
        @reset="resetConversation"
        @retry-health="checkHealth"
      />
      <ErrorBanner :message="error" @dismiss="setError('')" />
      <MessageList
        :generation-label="generationLabel"
        :generation-phase="generationPhase"
        :is-generating="isGenerating"
        :messages="messages"
      />
      <Composer
        :can-retry="canRetry"
        :draft="draft"
        :generation-label="generationLabel"
        :generation-phase="generationPhase"
        :is-generating="isGenerating"
        @retry="retryLastTurn"
        @stop="stopGeneration"
        @update:draft="setDraft"
        @submit="submitDraft"
      />
    </section>
  </main>
</template>
