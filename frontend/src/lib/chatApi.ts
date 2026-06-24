import type {
  ChatRequest,
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
  HealthResponse,
  StreamDoneEvent,
  StreamErrorEvent,
  StreamMessageEvent,
  StreamMetaEvent
} from "../types/chat";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function readErrorMessage(response: Response, fallbackMessage: string): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return fallbackMessage;
  }

  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function getJson<TResponse>(path: string, fallbackMessage: string): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`);

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, fallbackMessage));
  }

  return (await response.json()) as TResponse;
}

async function sendJson<TResponse>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  payload: unknown | undefined,
  fallbackMessage: string
): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers: payload === undefined
      ? undefined
      : {
          "Content-Type": "application/json"
        },
    body: payload === undefined ? undefined : JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, fallbackMessage));
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export function createChatReply(payload: ChatRequest): Promise<ChatResponse> {
  return sendJson<ChatResponse>("POST", "/api/chat", payload, "请求失败。");
}

interface StreamChatHandlers {
  onMeta?: (payload: StreamMetaEvent) => void;
  onMessage: (payload: StreamMessageEvent) => void;
  onError?: (payload: StreamErrorEvent) => void;
  onDone?: (payload: StreamDoneEvent) => void;
}

export interface StreamChatController {
  abort: () => void;
  completed: Promise<void>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health", "健康检查失败。");
}

export async function streamChatReply(
  payload: ChatRequest,
  handlers: StreamChatHandlers
): Promise<StreamChatController> {
  const abortController = new AbortController();

  const completed = (async () => {
    const response = await fetch(`${apiBaseUrl}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "X-Agent-Debug": "frontend-sse"
      },
      body: JSON.stringify(payload),
      signal: abortController.signal
    });

    if (!response.ok) {
      throw new Error(await readErrorMessage(response, `流式请求失败，状态码：${response.status}`));
    }

    if (!response.body) {
      throw new Error("浏览器未提供可读取的流式响应。");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        if (chunk.trim()) {
          parseSseChunk(chunk, handlers);
        }
      }
    }

    buffer += decoder.decode();

    if (buffer.trim()) {
      parseSseChunk(buffer, handlers);
    }
  })();

  return {
    abort: () => abortController.abort(),
    completed
  };
}

function parseSseChunk(chunk: string, handlers: StreamChatHandlers) {
  const lines = chunk
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const eventLine = lines.find((line) => line.startsWith("event:"));
  const dataLine = lines.find((line) => line.startsWith("data:"));

  if (!eventLine || !dataLine) {
    return;
  }

  const eventName = eventLine.slice("event:".length).trim();
  const jsonPayload = dataLine.slice("data:".length).trim();

  let payload: StreamMetaEvent | StreamMessageEvent | StreamErrorEvent | StreamDoneEvent;

  try {
    payload = JSON.parse(jsonPayload);
  } catch {
    return;
  }

  if (eventName === "meta") {
    handlers.onMeta?.(payload as StreamMetaEvent);
    return;
  }

  if (eventName === "message") {
    handlers.onMessage(payload as StreamMessageEvent);
    return;
  }

  if (eventName === "error") {
    handlers.onError?.(payload as StreamErrorEvent);
    return;
  }

  if (eventName === "done") {
    handlers.onDone?.(payload as StreamDoneEvent);
  }
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return getJson<ConversationSummary[]>("/api/conversations", "获取会话列表失败。");
}

export async function createConversation(title?: string): Promise<ConversationSummary> {
  return sendJson<ConversationSummary>(
    "POST",
    "/api/conversations",
    { title: title ?? "新对话" },
    "创建会话失败。"
  );
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return getJson<ConversationDetail>(`/api/conversations/${id}`, "获取会话详情失败。");
}

export async function updateConversationTitle(id: string, title: string): Promise<ConversationSummary> {
  return sendJson<ConversationSummary>(
    "PATCH",
    `/api/conversations/${id}`,
    { title },
    "更新会话标题失败。"
  );
}

export async function deleteConversation(id: string): Promise<void> {
  await sendJson<void>("DELETE", `/api/conversations/${id}`, undefined, "删除会话失败。");
}

export async function deleteLastTurn(id: string): Promise<ConversationSummary> {
  return sendJson<ConversationSummary>(
    "DELETE",
    `/api/conversations/${id}/last-turn`,
    undefined,
    "准备重试上一轮对话失败。"
  );
}
