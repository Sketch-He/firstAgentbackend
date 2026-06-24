import { onMounted, ref } from "vue";
import type { ConversationSummary } from "../types/chat";
import {
  createConversation as apiCreate,
  deleteConversation as apiDelete,
  listConversations
} from "../lib/chatApi";

function upsertConversation(
  conversations: ConversationSummary[],
  conversation: ConversationSummary
): ConversationSummary[] {
  return [conversation, ...conversations.filter((item) => item.id !== conversation.id)]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export function useConversation() {
  const conversations = ref<ConversationSummary[]>([]);
  const currentId = ref<string | null>(null);
  const isLoading = ref(false);
  const error = ref("");

  async function loadConversations() {
    isLoading.value = true;
    error.value = "";

    try {
      const nextConversations = await listConversations();
      conversations.value = nextConversations;

      if (currentId.value && !nextConversations.some((item) => item.id === currentId.value)) {
        currentId.value = null;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : "加载会话列表失败。";
    } finally {
      isLoading.value = false;
    }
  }

  async function createNew(): Promise<string | null> {
    try {
      const conversation = await apiCreate();
      conversations.value = upsertConversation(conversations.value, conversation);
      currentId.value = conversation.id;
      return conversation.id;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "创建会话失败。";
      return null;
    }
  }

  function select(id: string | null) {
    currentId.value = id;
  }

  async function remove(id: string) {
    try {
      await apiDelete(id);
      conversations.value = conversations.value.filter((item) => item.id !== id);

      if (currentId.value === id) {
        currentId.value = conversations.value[0]?.id ?? null;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : "删除会话失败。";
    }
  }

  function upsertSummary(conversation: ConversationSummary) {
    conversations.value = upsertConversation(conversations.value, conversation);
    if (!currentId.value) {
      currentId.value = conversation.id;
    }
  }

  onMounted(() => {
    void loadConversations();
  });

  return {
    conversations,
    currentId,
    isLoading,
    error,
    loadConversations,
    createNew,
    select,
    remove,
    upsertSummary
  };
}
