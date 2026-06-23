import { computed, ref, watch } from "vue";
import { streamChatReply } from "../lib/chatApi";
import type { ChatMessage, ChatRequestMessage } from "../types/chat";

const storageKey = "agent-demo-chat-messages";

const initialMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    content: "后端已经接入真实模型调用。你可以直接开始提问，我再继续和你一起完善交互和能力。"
  }
];

function toRequestMessages(messages: ChatMessage[]): ChatRequestMessage[] {
  return messages.map(({ role, content }) => ({ role, content }));
}

function createId() {
  return crypto.randomUUID();
}

function loadMessagesFromStorage(): ChatMessage[] {
  const rawValue = localStorage.getItem(storageKey);

  if (!rawValue) {
    return [...initialMessages];
  }

  try {
    const parsedValue = JSON.parse(rawValue) as ChatMessage[];

    if (!Array.isArray(parsedValue) || parsedValue.length === 0) {
      return [...initialMessages];
    }

    return parsedValue;
  } catch {
    return [...initialMessages];
  }
}

export function useChat() {
  const messages = ref<ChatMessage[]>(loadMessagesFromStorage());
  const draft = ref("");
  const isGenerating = ref(false);
  const error = ref("");
  const lastSubmittedContent = ref("");
  const currentAbort = ref<(() => void) | null>(null);
  const currentAssistantMessageId = ref("");
  const canRetry = computed(() => Boolean(lastSubmittedContent.value) && !isGenerating.value);

  // 先用本地存储保留最近一次会话，后面再按需要切数据库或服务端会话。
  watch(
    messages,
    (currentMessages) => {
      localStorage.setItem(storageKey, JSON.stringify(currentMessages));
    },
    { deep: true }
  );

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

    const nextMessages = [...messages.value, userMessage, assistantMessage];

    messages.value = nextMessages;
    draft.value = "";
    error.value = "";
    isGenerating.value = true;
    lastSubmittedContent.value = trimmedDraft;
    currentAssistantMessageId.value = assistantMessageId;

    try {
      const streamController = await streamChatReply(
        {
          // 发送给后端时不带刚创建的空 assistant 占位消息。
          messages: toRequestMessages([...messages.value].filter((message) => message.id !== assistantMessageId))
        },
        {
          onMessage: ({ delta }) => {
            messages.value = messages.value.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: `${message.content}${delta}`
                  }
                : message
            );
          },
          onError: ({ message }) => {
            throw new Error(message);
          },
          onDone: () => {
            const targetMessage = messages.value.find((message) => message.id === assistantMessageId);

            if (!targetMessage?.content.trim()) {
              throw new Error("模型没有返回有效内容。");
            }
          }
        }
      );

      currentAbort.value = streamController.abort;
      await streamController.completed;
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") {
        error.value = "本次生成已停止。";
      } else {
        messages.value = messages.value.filter((message) => message.id !== assistantMessageId);
        error.value =
          requestError instanceof Error
            ? requestError.message
            : "发生了未知请求错误。";
      }
    } finally {
      currentAbort.value = null;
      currentAssistantMessageId.value = "";
      isGenerating.value = false;
    }
  }

  async function retryLastTurn() {
    if (!lastSubmittedContent.value || isGenerating.value) {
      return;
    }

    // 重试前清掉上一轮对应的助手回复，避免连续保留失败或中断结果。
    const reversedMessages = [...messages.value].reverse();
    const lastAssistantMessage = reversedMessages.find((message) => message.role === "assistant");

    if (lastAssistantMessage && lastAssistantMessage.id !== "welcome") {
      messages.value = messages.value.filter((message) => message.id !== lastAssistantMessage.id);
    }

    draft.value = lastSubmittedContent.value;
    await submitDraft();
  }

  function stopGeneration() {
    currentAbort.value?.();
  }

  function resetConversation() {
    messages.value = [...initialMessages];
    localStorage.removeItem(storageKey);
    draft.value = "";
    error.value = "";
    lastSubmittedContent.value = "";
    currentAbort.value?.();
    currentAbort.value = null;
    currentAssistantMessageId.value = "";
    isGenerating.value = false;
  }

  function setDraft(value: string) {
    draft.value = value;
  }

  function setError(value: string) {
    error.value = value;
  }

  return {
    canRetry,
    draft,
    error,
    isGenerating,
    lastSubmittedContent,
    messages,
    resetConversation,
    retryLastTurn,
    setDraft,
    setError,
    stopGeneration,
    submitDraft
  };
}
