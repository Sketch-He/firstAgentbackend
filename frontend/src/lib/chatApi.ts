import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  StreamDoneEvent,
  StreamErrorEvent,
  StreamMessageEvent,
  StreamMetaEvent
} from "../types/chat";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

// 统一保留一个最小请求封装，后续接鉴权、超时和 SSE 时会更好扩展。
async function postJson<TResponse>(
  path: string,
  payload: unknown
): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, `请求失败，状态码：${response.status}`));
  }

  return (await response.json()) as TResponse;
}

export function createChatReply(payload: ChatRequest): Promise<ChatResponse> {
  return postJson<ChatResponse>("/api/chat", payload);
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
  const response = await fetch(`${apiBaseUrl}/health`);

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, `健康检查失败，状态码：${response.status}`));
  }

  return (await response.json()) as HealthResponse;
}

export async function streamChatReply(
  payload: ChatRequest,
  handlers: StreamChatHandlers
) : Promise<StreamChatController> {
  const abortController = new AbortController();

  const completed = (async () => {
    // 前端这里发的是 POST + SSE，不是普通 EventSource。
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

    // 按 SSE 的空行分隔事件块，再解析 event/data 两行。
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        parseSseChunk(chunk, handlers);
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
  const payload = JSON.parse(jsonPayload) as
    | StreamMetaEvent
    | StreamMessageEvent
    | StreamErrorEvent
    | StreamDoneEvent;

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
