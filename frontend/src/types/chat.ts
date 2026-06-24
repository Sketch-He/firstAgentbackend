export type ChatRole = "system" | "user" | "assistant" | "tool";
export type GenerationPhase =
  | "idle"
  | "submitting"
  | "awaiting"
  | "streaming"
  | "stopping";

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

export interface HealthResponse {
  status: string;
  service: string;
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
