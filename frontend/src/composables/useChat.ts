import { computed, ref } from "vue";
import { deleteLastTurn, streamChatReply } from "../lib/chatApi";
import type {
  ChatMessage,
  ChatRequestMessage,
  ConversationMessage,
  ConversationSummary,
  GenerationPhase
} from "../types/chat";

const welcomeMessage: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "后端已经接入真实模型调用。你可以直接开始提问，我再继续和你一起完善交互和能力。"
};

function toRequestMessages(messages: ChatMessage[]): ChatRequestMessage[] {
  return messages.map(({ role, content }) => ({ role, content }));
}

function createId() {
  return crypto.randomUUID();
}

function toDisplayMessages(conversationMessages: ConversationMessage[]): ChatMessage[] {
  const nextMessages = conversationMessages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content
  }));

  return nextMessages.length > 0 ? nextMessages : [welcomeMessage];
}

interface UseChatOptions {
  onConversationSync?: (conversation: ConversationSummary) => void;
  refreshConversations?: () => Promise<void>;
}

export function useChat(options?: UseChatOptions) {
  const messages = ref<ChatMessage[]>([welcomeMessage]);
  const draft = ref("");
  const isGenerating = ref(false);
  const generationPhase = ref<GenerationPhase>("idle");
  const error = ref("");
  const lastSubmittedContent = ref("");
  const currentAbort = ref<(() => void) | null>(null);
  const currentAssistantMessageId = ref("");
  const currentConversationId = ref<string | null>(null);
  const canRetry = computed(() => Boolean(lastSubmittedContent.value) && !isGenerating.value);
  const generationLabel = computed(() => {
    switch (generationPhase.value) {
      case "submitting":
        return "正在发送请求";
      case "awaiting":
        return "模型思考中";
      case "streaming":
        return "正在生成回复";
      case "stopping":
        return "正在停止生成";
      default:
        return "等待提问";
    }
  });

  async function loadConversation(conversationId: string, conversationMessages: ConversationMessage[]) {
    currentConversationId.value = conversationId;
    messages.value = toDisplayMessages(conversationMessages);
    draft.value = "";
    error.value = "";
    lastSubmittedContent.value = "";
    currentAbort.value = null;
    currentAssistantMessageId.value = "";
    isGenerating.value = false;
    generationPhase.value = "idle";
  }

  function resetToNew() {
    currentConversationId.value = null;
    messages.value = [welcomeMessage];
    draft.value = "";
    error.value = "";
    lastSubmittedContent.value = "";
    currentAbort.value?.();
    currentAbort.value = null;
    currentAssistantMessageId.value = "";
    isGenerating.value = false;
    generationPhase.value = "idle";
  }

  async function submitDraft() {
    const trimmedDraft = draft.value.trim();

    if (!trimmedDraft || isGenerating.value) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmedDraft
    };

    const assistantMessageId = createId();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: ""
    };

    messages.value = [...messages.value, userMessage, assistantMessage];
    draft.value = "";
    error.value = "";
    isGenerating.value = true;
    generationPhase.value = "submitting";
    lastSubmittedContent.value = trimmedDraft;
    currentAssistantMessageId.value = assistantMessageId;

    let streamErrorMessage = "";

    try {
      const streamController = await streamChatReply(
        {
          messages: toRequestMessages(messages.value.filter((message) => message.id !== assistantMessageId)),
          conversation_id: currentConversationId.value ?? undefined
        },
        {
          onMeta: (payload) => {
            generationPhase.value = "awaiting";

            if (payload.conversation) {
              currentConversationId.value = payload.conversation.id;
              options?.onConversationSync?.(payload.conversation);
            }
          },
          onMessage: ({ delta }) => {
            generationPhase.value = "streaming";
            messages.value = messages.value.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: `${message.content}${delta}` }
                : message
            );
          },
          onError: ({ message }) => {
            streamErrorMessage = message;
          },
          onDone: (payload) => {
            if (payload.conversation) {
              currentConversationId.value = payload.conversation.id;
              options?.onConversationSync?.(payload.conversation);
            }
          }
        }
      );

      currentAbort.value = streamController.abort;
      generationPhase.value = "awaiting";
      await streamController.completed;

      const finalMessage = messages.value.find((message) => message.id === assistantMessageId);
      if (!finalMessage?.content.trim() && !streamErrorMessage) {
        throw new Error("模型没有返回有效内容。");
      }

      if (streamErrorMessage) {
        throw new Error(streamErrorMessage);
      }
    } catch (requestError) {
      const targetMessage = messages.value.find((message) => message.id === assistantMessageId);
      const hasAssistantContent = Boolean(targetMessage?.content.trim());

      if (requestError instanceof DOMException && requestError.name === "AbortError") {
        if (!hasAssistantContent) {
          messages.value = messages.value.filter((message) => message.id !== assistantMessageId);
        }

        error.value = "本次生成已停止。";

        if (currentConversationId.value) {
          await options?.refreshConversations?.();
        }
      } else {
        if (!hasAssistantContent) {
          messages.value = messages.value.filter((message) => message.id !== assistantMessageId);
        }

        error.value = requestError instanceof Error ? requestError.message : "发生了未知请求错误。";

        if (currentConversationId.value) {
          await options?.refreshConversations?.();
        }
      }
    } finally {
      currentAbort.value = null;
      currentAssistantMessageId.value = "";
      isGenerating.value = false;
      generationPhase.value = "idle";
    }
  }

  async function retryLastTurn() {
    if (!lastSubmittedContent.value || isGenerating.value) {
      return;
    }

    if (currentConversationId.value) {
      try {
        const updatedConversation = await deleteLastTurn(currentConversationId.value);
        options?.onConversationSync?.(updatedConversation);
      } catch (e) {
        error.value = e instanceof Error ? e.message : "准备重试上一轮对话失败。";
        await options?.refreshConversations?.();
        return;
      }
    }

    const reversedMessages = [...messages.value].reverse();
    const lastAssistantMessage = reversedMessages.find((message) => message.role === "assistant");
    const lastUserMessage = reversedMessages.find((message) => message.role === "user");

    if (lastAssistantMessage && lastAssistantMessage.id !== "welcome") {
      messages.value = messages.value.filter((message) => message.id !== lastAssistantMessage.id);
    }

    if (lastUserMessage && lastUserMessage.content === lastSubmittedContent.value) {
      messages.value = messages.value.filter((message) => message.id !== lastUserMessage.id);
    }

    if (messages.value.length === 0) {
      messages.value = [welcomeMessage];
    }

    draft.value = lastSubmittedContent.value;
    await submitDraft();
  }

  function stopGeneration() {
    generationPhase.value = "stopping";
    currentAbort.value?.();
  }

  function setDraft(value: string) {
    draft.value = value;
  }

  function setError(value: string) {
    error.value = value;
  }

  return {
    canRetry,
    currentConversationId,
    draft,
    error,
    generationLabel,
    generationPhase,
    isGenerating,
    lastSubmittedContent,
    messages,
    loadConversation,
    resetToNew,
    retryLastTurn,
    setDraft,
    setError,
    stopGeneration,
    submitDraft
  };
}
