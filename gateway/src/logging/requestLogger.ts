import type { TokenUsage } from "../types/openai.js";

type RequestLog = {
  alias: string;
  provider: string;
  latencyMs: number;
  usage?: TokenUsage;
};

export function logRequest(entry: RequestLog): void {
  console.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      modelAlias: entry.alias,
      provider: entry.provider,
      latencyMs: entry.latencyMs,
      usage: entry.usage ?? null
    })
  );
}
