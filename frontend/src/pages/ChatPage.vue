<script setup lang="ts">
import { ref, watch } from "vue";
import Composer from "../components/Composer.vue";
import Header from "../components/Header.vue";
import KnowledgePanel from "../components/KnowledgePanel.vue";
import MessageList from "../components/MessageList.vue";
import Sidebar from "../components/Sidebar.vue";
import { useChat } from "../composables/useChat";
import { useConversation } from "../composables/useConversation";
import { useDocuments } from "../composables/useDocuments";
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

const {
  documents,
  isLoading: isLoadingDocuments,
  isUploading,
  loadDocuments,
  uploadDocument,
  deleteDocument,
  retryDocument
} = useDocuments();

const showKnowledgePanel = ref(false);

function syncConversation(conversation: ConversationSummary) {
  upsertSummary(conversation);
  select(conversation.id);
}

const {
  canRetry,
  currentConversationId,
  draft,
  generationLabel,
  generationPhase,
  isGenerating,
  messages,
  messageSources,
  ragMode,
  loadConversation,
  resetToNew,
  retryLastTurn,
  setDraft,
  setError,
  setRagMode,
  stopGeneration,
  submitDraft
} = useChat({
  onConversationSync: syncConversation,
  refreshConversations: loadConversations
});

const hasReadyDocuments = ref(false);

// 监听文档列表变化，更新 hasReadyDocuments
watch(documents, (docs) => {
  hasReadyDocuments.value = docs.some((d) => d.status === "ready");
}, { immediate: true });

async function handleDocumentUpload(file: File) {
  await uploadDocument(file);
}

async function handleDocumentDelete(id: string) {
  await deleteDocument(id);
}

async function handleDocumentRetry(id: string) {
  await retryDocument(id);
}

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

function handleKnowledgePanel() {
  showKnowledgePanel.value = !showKnowledgePanel.value;
}
</script>

<template>
  <main class="app-shell">
    <div class="layout-shell">
      <Sidebar
        :conversations="conversations"
        :current-id="currentId ?? currentConversationId"
        :is-loading="isLoadingConversations"
        @create="handleCreate"
        @select="handleSelect"
        @delete="handleDelete"
        @knowledge="showKnowledgePanel = !showKnowledgePanel"
      />

      <KnowledgePanel
        v-if="showKnowledgePanel"
        :documents="documents"
        :is-loading="isLoadingDocuments"
        :is-uploading="isUploading"
        @upload="handleDocumentUpload"
        @delete="handleDocumentDelete"
        @retry="handleDocumentRetry"
        @close="showKnowledgePanel = false"
      />

      <section class="chat-shell">
        <div class="chat-stage">
          <!-- <Header /> -->
          <MessageList
            :generation-label="generationLabel"
            :generation-phase="generationPhase"
            :is-generating="isGenerating"
            :messages="messages"
            :message-sources="messageSources"
          />
          <Composer
            :can-retry="canRetry"
            :draft="draft"
            :generation-label="generationLabel"
            :generation-phase="generationPhase"
            :is-generating="isGenerating"
            :rag-mode="ragMode"
            :has-documents="hasReadyDocuments"
            @retry="retryLastTurn"
            @stop="stopGeneration"
            @update:draft="setDraft"
            @update:rag-mode="setRagMode"
            @submit="submitDraft"
          />
        </div>
      </section>
    </div>
  </main>
</template>
