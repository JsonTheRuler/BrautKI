import type { ChatCompletionRequest, ChatCompletionResponse } from "../types/openai.js";
import type { ModelConfig, Provider } from "./base.js";
import { fetchWithRetry } from "./httpClient.js";

export class AnthropicProvider implements Provider {
  async complete(req: ChatCompletionRequest, cfg: ModelConfig): Promise<ChatCompletionResponse> {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) throw new Error("ANTHROPIC_API_KEY is missing.");

    const systemMessages = req.messages.filter((msg) => msg.role === "system").map((msg) => msg.content);
    const nonSystem = req.messages
      .filter((msg) => msg.role !== "system")
      .map((msg) => ({ role: msg.role === "assistant" ? "assistant" : "user", content: msg.content }));

    const response = await fetchWithRetry("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: cfg.providerModel,
        max_tokens: req.max_tokens ?? 512,
        temperature: req.temperature,
        system: systemMessages.join("\n"),
        messages: nonSystem
      })
    });

    if (!response.ok) {
      throw new Error(`Anthropic request failed: ${response.status} ${await response.text()}`);
    }

    const data = (await response.json()) as {
      id: string;
      model: string;
      content: Array<{ type: string; text?: string }>;
      usage?: { input_tokens?: number; output_tokens?: number };
      stop_reason?: string;
    };

    const text = data.content.find((item) => item.type === "text")?.text ?? "";
    return {
      id: data.id,
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: data.model,
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: text },
          finish_reason: data.stop_reason ?? "stop"
        }
      ],
      usage: {
        prompt_tokens: data.usage?.input_tokens,
        completion_tokens: data.usage?.output_tokens,
        total_tokens:
          (data.usage?.input_tokens ?? 0) + (data.usage?.output_tokens ?? 0) || undefined
      }
    };
  }
}
