import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { z } from "zod";
import type { ModelConfig } from "../providers/base.js";

const modelSchema = z.object({
  provider: z.enum(["openai", "anthropic", "openrouter", "local-http"]),
  providerModel: z.string(),
  baseUrl: z.string().optional(),
  path: z.string().optional(),
  headers: z.record(z.string()).optional()
});

const modelsFileSchema = z.object({
  models: z.record(modelSchema)
});

function resolveEnv(input: string): string {
  return input.replace(/\$\{([^}]+)\}/g, (_, token: string) => {
    const [key, fallback] = token.split(":-");
    const envValue = process.env[key];
    if (envValue && envValue.length > 0) {
      return envValue;
    }
    return fallback ?? "";
  });
}

export function loadModelsConfig(filePath = path.resolve(process.cwd(), "models.yml")): Record<string, ModelConfig> {
  const raw = fs.readFileSync(filePath, "utf8");
  const parsedYaml = yaml.load(raw);
  const parsed = modelsFileSchema.parse(parsedYaml);

  const resolved: Record<string, ModelConfig> = {};
  for (const [alias, cfg] of Object.entries(parsed.models)) {
    resolved[alias] = {
      ...cfg,
      baseUrl: cfg.baseUrl ? resolveEnv(cfg.baseUrl) : undefined,
      path: cfg.path ? resolveEnv(cfg.path) : undefined
    };
  }
  return resolved;
}
