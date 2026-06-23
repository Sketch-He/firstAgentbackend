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
}

export interface ChatResponse {
  reply: ChatRequestMessage;
  meta: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface StreamMetaEvent {
  mode: string;
  provider?: string;
  model?: string;
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
}
