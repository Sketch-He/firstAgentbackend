<script setup lang="ts">
import { watch } from "vue";
import Composer from "../components/Composer.vue";
import ErrorBanner from "../components/ErrorBanner.vue";
import Header from "../components/Header.vue";
import MessageList from "../components/MessageList.vue";
import Sidebar from "../components/Sidebar.vue";
import { useChat } from "../composables/useChat";
import { useConversation } from "../composables/useConversation";
import { useServiceHealth } from "../composables/useServiceHealth";
import { getConversation } from "../lib/chatApi";
import type { ConversationSummary } from "../types/chat";

const {
  conversations,
  currentId,
  isLoading: isLoadingConversations,
  remove,
  select,
  loadConversations,
  upsertSummary
} = useConversation();

function syncConversation(conversation: ConversationSummary) {
  upsertSummary(conversation);
  select(conversation.id);
}

const {
  canRetry,
  currentConversationId,
  draft,
  error: chatError,
  generationLabel,
  generationPhase,
  isGenerating,
  latestStreamMeta,
  messages,
  loadConversation,
  resetToNew,
  retryLastTurn,
  setDraft,
  setError,
  stopGeneration,
  submitDraft
} = useChat({
  onConversationSync: syncConversation,
  refreshConversations: loadConversations
});

const { checkHealth, serviceName, status } = useServiceHealth();

let latestLoadVersion = 0;

watch(currentId, async (newId, _oldId, onCleanup) => {
  if (!newId) {
    resetToNew();
    return;
  }

  if (isGenerating.value) {
    return;
  }

  const loadVersion = ++latestLoadVersion;
  let cancelled = false;

  onCleanup(() => {
    cancelled = true;
  });

  try {
    const detail = await getConversation(newId);
    if (cancelled || loadVersion !== latestLoadVersion || currentId.value !== newId) {
      return;
    }

    await loadConversation(detail.id, detail.messages);
  } catch (e) {
    if (cancelled) {
      return;
    }

    setError(e instanceof Error ? e.message : "加载会话失败。");
  }
});

function handleCreate() {
  if (isGenerating.value) {
    return;
  }

  select(null);
  resetToNew();
}

function handleSelect(id: string) {
  if (isGenerating.value) {
    return;
  }

  select(id);
}

async function handleDelete(id: string) {
  if (isGenerating.value) {
    return;
  }

  await remove(id);

  if (!currentId.value) {
    resetToNew();
  }
}

function handleReset() {
  if (isGenerating.value) {
    return;
  }

  select(null);
  resetToNew();
}
</script>

<template>
  <main class="app-shell">
    <div class="glow glow-left" />
    <div class="glow glow-right" />

    <div class="layout-shell">
      <Sidebar
        :conversations="conversations"
        :current-id="currentId ?? currentConversationId"
        :is-loading="isLoadingConversations"
        @create="handleCreate"
        @select="handleSelect"
        @delete="handleDelete"
      />

      <section class="chat-shell">
        <div class="chat-stage">
          <Header
            :generation-label="generationLabel"
            :generation-phase="generationPhase"
            :is-generating="isGenerating"
            :model-name="latestStreamMeta?.model ?? ''"
            :service-name="serviceName"
            :service-status="status"
            @reset="handleReset"
            @retry-health="checkHealth"
          />
          <!-- <ErrorBanner :message="chatError" @dismiss="setError('')" /> -->
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
        </div>
      </section>
    </div>
  </main>
</template>
