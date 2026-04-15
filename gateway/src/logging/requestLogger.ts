import type { TokenUsage } from "../types/openai.js";

type RequestLog = {
  requestId?: string;
  alias: string;
  provider: string;
  latencyMs: number;
  usage?: TokenUsage;
};

export function logRequest(entry: RequestLog): void {
  console.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      category: "request",
      requestId: entry.requestId ?? null,
      modelAlias: entry.alias,
      provider: entry.provider,
      latencyMs: entry.latencyMs,
      usage: entry.usage ?? null
    })
  );
}
