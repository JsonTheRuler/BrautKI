import type { ChatCompletionRequest, ChatCompletionResponse } from "../types/openai.js";
import type { ModelConfig, Provider } from "./base.js";
import { fetchWithRetry } from "./httpClient.js";

export class OpenRouterProvider implements Provider {
  async complete(req: ChatCompletionRequest, cfg: ModelConfig): Promise<ChatCompletionResponse> {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) throw new Error("OPENROUTER_API_KEY is missing.");

    const response = await fetchWithRetry("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: cfg.providerModel,
        messages: req.messages,
        temperature: req.temperature,
        max_tokens: req.max_tokens
      })
    });

    if (!response.ok) {
      throw new Error(`OpenRouter request failed: ${response.status} ${await response.text()}`);
    }

    return (await response.json()) as ChatCompletionResponse;
  }
}
