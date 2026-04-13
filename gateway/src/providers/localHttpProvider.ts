import type { ChatCompletionRequest, ChatCompletionResponse } from "../types/openai.js";
import type { ModelConfig, Provider } from "./base.js";

export class LocalHttpProvider implements Provider {
  async complete(req: ChatCompletionRequest, cfg: ModelConfig): Promise<ChatCompletionResponse> {
    if (!cfg.baseUrl || !cfg.path) {
      throw new Error("LocalHttpProvider requires baseUrl and path in model config.");
    }

    const url = new URL(cfg.path, cfg.baseUrl).toString();
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(cfg.headers ?? {})
      },
      body: JSON.stringify({
        model: cfg.providerModel,
        messages: req.messages,
        temperature: req.temperature,
        max_tokens: req.max_tokens,
        metadata: req.metadata
      })
    });

    if (!response.ok) {
      throw new Error(`Local HTTP provider request failed: ${response.status} ${await response.text()}`);
    }

    return (await response.json()) as ChatCompletionResponse;
  }
}
