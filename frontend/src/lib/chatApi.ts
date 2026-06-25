import type {
  ApiResponse,
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

/** 业务错误，包含后端返回的 code 和 message。 */
export class ApiError extends Error {
  code: number;

  constructor(code: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

async function readErrorMessage(response: Response, fallbackMessage: string): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return fallbackMessage;
  }

  try {
    const payload = (await response.json()) as { detail?: string; message?: string };
    return payload.message || payload.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

/**
 * 解析统一 ApiResponse，成功时返回 data，失败时抛出 ApiError。
 * HTTP 状态码非 2xx 时走 readErrorMessage 降级处理。
 */
async function unwrapResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) {
    // HTTP 层面的错误（如 422 参数校验失败），尝试从 ApiResponse 格式读取。
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      try {
        const body = (await response.json()) as ApiResponse<T>;
        if (body.code !== undefined) {
          throw new ApiError(body.code, body.message || fallbackMessage);
        }
      } catch (e) {
        if (e instanceof ApiError) throw e;
      }
    }
    // 降级：非 ApiResponse 格式的错误响应。
    throw new Error(await readErrorMessage(response, fallbackMessage));
  }

  if (response.status === 204) {
    // 理论上不应该再有 204 了（已改为 200），但做防御性处理。
    return undefined as T;
  }

  const body = (await response.json()) as ApiResponse<T>;

  if (body.code !== 0) {
    throw new ApiError(body.code, body.message || fallbackMessage);
  }

  return (body.data ?? undefined) as T;
}

async function getJson<TResponse>(path: string, fallbackMessage: string): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  return unwrapResponse<TResponse>(response, fallbackMessage);
}

async function sendJson<TResponse>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  payload: unknown | undefined,
  fallbackMessage: string
): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers:
      payload === undefined
        ? undefined
        : {
            "Content-Type": "application/json"
          },
    body: payload === undefined ? undefined : JSON.stringify(payload)
  });

  return unwrapResponse<TResponse>(response, fallbackMessage);
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
      // 流式请求的初始 HTTP 错误也尝试解析 ApiResponse 格式。
      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/json")) {
        try {
          const body = (await response.json()) as ApiResponse;
          if (body.code !== undefined) {
            throw new ApiError(body.code, body.message || `流式请求失败，状态码：${response.status}`);
          }
        } catch (e) {
          if (e instanceof ApiError) throw e;
        }
      }
      throw new Error(
        await readErrorMessage(response, `流式请求失败，状态码：${response.status}`)
      );
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

export async function updateConversationTitle(
  id: string,
  title: string
): Promise<ConversationSummary> {
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
