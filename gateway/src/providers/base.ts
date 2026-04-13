import type { ChatCompletionRequest, ChatCompletionResponse } from "../types/openai.js";

export type ProviderType = "openai" | "anthropic" | "openrouter" | "local-http";

export type ModelConfig = {
  provider: ProviderType;
  providerModel: string;
  baseUrl?: string;
  path?: string;
  headers?: Record<string, string>;
};

export interface Provider {
  complete(req: ChatCompletionRequest, cfg: ModelConfig): Promise<ChatCompletionResponse>;
}
