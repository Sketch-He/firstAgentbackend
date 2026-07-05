export type ChatRole = "system" | "user" | "assistant" | "tool";
export type GenerationPhase =
  | "idle"
  | "submitting"
  | "awaiting"
  | "streaming"
  | "stopping";

/** 统一 API 响应包装，与后端 ApiResponse 对应。 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T | null;
}

/** 业务错误码常量，与后端 ErrorCode 对应。 */
export const ErrorCode = {
  SUCCESS: 0,
  NOT_FOUND: 10001,
  BAD_REQUEST: 10002,
  CONFLICT: 10003,
  LLM_CONFIG_ERROR: 20001,
  LLM_RATE_LIMIT: 20002,
  LLM_CONNECTION_ERROR: 20003,
  LLM_SERVICE_ERROR: 20004,
  UNKNOWN: 99999
} as const;

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

export interface ChatRequestMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequest {
  messages: ChatRequestMessage[];
  conversation_id?: string;
}

export interface ChatResponse {
  reply: ChatRequestMessage;
  meta: Record<string, unknown>;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface StreamMetaEvent {
  mode: string;
  provider?: string;
  model?: string;
  conversation?: ConversationSummary;
}

export interface StreamMessageEvent {
  delta: string;
}

export interface StreamErrorEvent {
  message: string;
  status_code?: number;
}

export interface StreamDoneEvent {
  finish_reason: string;
  conversation?: ConversationSummary;
}

export interface ConversationMessage {
  id: string;
  role: ChatRole;
  content: string;
  sort_order: number;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ConversationMessage[];
}

// 文档相关类型
export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: "processing" | "ready" | "failed";
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
}

export type RagMode = "auto" | "always" | "never";

export interface RagChatRequest {
  messages: ChatRequestMessage[];
  conversation_id?: string;
  rag_mode: RagMode;
  top_k?: number;
}

export interface RagSource {
  document_id: string;
  filename: string;
  chunk_index: number;
  snippet: string;
}

export interface StreamSourceEvent {
  document_id: string;
  filename: string;
  chunk_index: number;
  snippet: string;
}
