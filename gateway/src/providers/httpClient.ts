export type HttpRetryOptions = {
  timeoutMs?: number;
  retries?: number;
  retryDelayMs?: number;
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchWithRetry(
  url: string,
  init: RequestInit,
  options: HttpRetryOptions = {}
): Promise<Response> {
  const timeoutMs = options.timeoutMs ?? 30_000;
  const retries = options.retries ?? 2;
  const retryDelayMs = options.retryDelayMs ?? 400;
  let lastError: unknown;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      const response = await fetch(url, { ...init, signal: controller.signal });
      clearTimeout(timeout);
      if (response.ok || response.status < 500 || attempt === retries) {
        return response;
      }
      await sleep(retryDelayMs * (attempt + 1));
    } catch (error) {
      lastError = error;
      if (attempt === retries) break;
      await sleep(retryDelayMs * (attempt + 1));
    }
  }

  throw new Error(
    `Request failed after retries: ${
      lastError instanceof Error ? lastError.message : "Unknown network error"
    }`
  );
}
