type Counters = Record<string, number>;

const counters: Counters = {
  requestsTotal: 0,
  chatCompletionsTotal: 0,
  chatCompletionsFailed: 0,
  authFailures: 0,
  rateLimited: 0
};

export function incMetric(name: keyof typeof counters, by = 1): void {
  counters[name] += by;
}

export function getMetricsSnapshot() {
  return {
    generatedAt: new Date().toISOString(),
    counters: { ...counters }
  };
}
