import "dotenv/config";
import express from "express";
import path from "node:path";
import { z } from "zod";
import { loadModelsConfig } from "./config/loadModels.js";
import { logRequest } from "./logging/requestLogger.js";
import { resolveProvider } from "./router/resolveProvider.js";

const app = express();
app.use(express.json({ limit: "2mb" }));
app.use("/admin/static", express.static(path.resolve(process.cwd(), "src/admin")));
const adminCorsOrigin = process.env.ADMIN_CORS_ORIGIN ?? "*";
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", adminCorsOrigin);
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
  res.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  if (req.method === "OPTIONS") {
    return res.sendStatus(204);
  }
  next();
});

const integrationTargets = {
  gateway: process.env.GATEWAY_SELF_URL ?? `http://localhost:${process.env.PORT ?? 4000}`,
  agents: process.env.AGENTS_BASE_URL ?? "http://localhost:8010",
  council: process.env.COUNCIL_BASE_URL ?? "http://localhost:8088",
  n8n: process.env.N8N_BASE_URL ?? "http://localhost:5678",
  gemmaWrapper: process.env.LOCAL_GEMMA_BASE_URL ?? "http://localhost:11500",
  karpathy: process.env.KARPATHY_BASE_URL ?? "http://localhost:11600"
};

const requestSchema = z.object({
  model: z.string(),
  messages: z.array(
    z.object({
      role: z.enum(["system", "user", "assistant", "tool"]),
      content: z.string()
    })
  ),
  temperature: z.number().optional(),
  max_tokens: z.number().int().positive().optional(),
  metadata: z.record(z.unknown()).optional()
});

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "ai-ready-gateway" });
});

app.get("/admin", (_req, res) => {
  res.sendFile(path.resolve(process.cwd(), "src/admin/index.html"));
});

app.get("/admin/integrations/health", async (_req, res) => {
  const checks = await Promise.all(
    Object.entries(integrationTargets).map(async ([name, base]) => {
      const healthUrl = name === "n8n" ? `${base}/healthz` : `${base}/health`;
      const started = Date.now();
      try {
        const response = await fetch(healthUrl, { method: "GET" });
        return {
          name,
          base,
          ok: response.ok,
          status: response.status,
          latencyMs: Date.now() - started
        };
      } catch (error) {
        return {
          name,
          base,
          ok: false,
          status: 0,
          latencyMs: Date.now() - started,
          error: error instanceof Error ? error.message : "Unknown error"
        };
      }
    })
  );
  res.json({ generatedAt: new Date().toISOString(), checks });
});

const actionSchema = z.object({
  action: z.enum(["runInbox", "runCrm", "runMarketing", "runDelivery", "runCouncilDemo"]),
  payload: z.record(z.unknown()).optional()
});

app.post("/admin/actions/run", async (req, res) => {
  const parsed = actionSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid action body", details: parsed.error.flatten() });
  }

  const payload = parsed.data.payload ?? {};
  try {
    if (parsed.data.action === "runInbox") {
      const response = await fetch(`${integrationTargets.agents}/agents/inbox/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_limit: 10, ...payload })
      });
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runCrm") {
      const response = await fetch(`${integrationTargets.agents}/agents/crm/run`, { method: "POST" });
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runMarketing") {
      const response = await fetch(`${integrationTargets.agents}/agents/marketing/run`, { method: "POST" });
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runDelivery") {
      const response = await fetch(`${integrationTargets.agents}/agents/delivery/run`, { method: "POST" });
      return res.status(response.status).json(await response.json());
    }

    const councilPayload = {
      question: "Give a concise executive summary of current AI operations posture.",
      context: { source: "gateway-admin-ui", timestamp: new Date().toISOString() }
    };
    const councilResponse = await fetch(`${integrationTargets.council}/council/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(councilPayload)
    });
    return res.status(councilResponse.status).json(await councilResponse.json());
  } catch (error) {
    return res.status(502).json({
      error: error instanceof Error ? error.message : "Action execution failed."
    });
  }
});

app.post("/v1/chat/completions", async (req, res) => {
  const parsed = requestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Invalid request body", details: parsed.error.flatten() });
  }

  const models = loadModelsConfig();
  const modelCfg = models[parsed.data.model];
  if (!modelCfg) {
    return res.status(404).json({ error: `Unknown model alias: ${parsed.data.model}` });
  }

  const started = Date.now();
  try {
    const provider = resolveProvider(modelCfg.provider);
    const response = await provider.complete(parsed.data, modelCfg);

    logRequest({
      alias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started,
      usage: response.usage
    });

    return res.json({
      ...response,
      model: parsed.data.model
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown gateway error.";
    logRequest({
      alias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started
    });
    return res.status(502).json({ error: message });
  }
});

const port = Number(process.env.PORT ?? 4000);
app.listen(port, () => {
  console.log(`Gateway listening on http://localhost:${port}`);
});
