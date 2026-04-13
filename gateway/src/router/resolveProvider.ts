import type { Provider, ProviderType } from "../providers/base.js";
import { AnthropicProvider } from "../providers/anthropicProvider.js";
import { LocalHttpProvider } from "../providers/localHttpProvider.js";
import { OpenAIProvider } from "../providers/openaiProvider.js";
import { OpenRouterProvider } from "../providers/openRouterProvider.js";

const registry: Record<ProviderType, Provider> = {
  openai: new OpenAIProvider(),
  anthropic: new AnthropicProvider(),
  openrouter: new OpenRouterProvider(),
  "local-http": new LocalHttpProvider()
};

export function resolveProvider(providerType: ProviderType): Provider {
  return registry[providerType];
}
