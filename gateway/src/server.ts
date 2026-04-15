import "dotenv/config";
import express from "express";
import path from "node:path";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import { z } from "zod";
import { loadModelsConfig } from "./config/loadModels.js";
import { getMetricsSnapshot, incMetric } from "./logging/metrics.js";
import { logRequest } from "./logging/requestLogger.js";
import { fetchWithRetry } from "./providers/httpClient.js";
import { resolveProvider } from "./router/resolveProvider.js";

const app = express();
app.use(express.json({ limit: "2mb" }));
app.use("/admin/static", express.static(path.resolve(process.cwd(), "src/admin")));
const adminCorsOrigin = process.env.ADMIN_CORS_ORIGIN ?? "*";
const adminApiKey = process.env.ADMIN_API_KEY ?? "";
const gatewayApiKey = process.env.GATEWAY_API_KEY ?? "";
const secureMode = (process.env.SECURE_MODE ?? "false").toLowerCase() === "true";
const trustForwardedIp = (process.env.TRUST_PROXY ?? "false").toLowerCase() === "true";
if (trustForwardedIp) {
  app.set("trust proxy", 1);
}

type RateLimitBucket = { count: number; resetAt: number };
const rateLimitStore = new Map<string, RateLimitBucket>();
const parsedLimitWindowMs = Number(process.env.RATE_LIMIT_WINDOW_MS ?? 60_000);
const parsedLimitMax = Number(process.env.RATE_LIMIT_MAX ?? 120);
const parsedDownstreamTimeoutMs = Number(process.env.DOWNSTREAM_TIMEOUT_MS ?? 20_000);
const parsedDownstreamRetries = Number(process.env.DOWNSTREAM_RETRIES ?? 2);
const defaultLimitWindowMs = Number.isFinite(parsedLimitWindowMs) ? parsedLimitWindowMs : 60_000;
const defaultLimitMax = Number.isFinite(parsedLimitMax) ? parsedLimitMax : 120;
const downstreamTimeoutMs = Number.isFinite(parsedDownstreamTimeoutMs) ? parsedDownstreamTimeoutMs : 20_000;
const downstreamRetries = Number.isFinite(parsedDownstreamRetries) ? parsedDownstreamRetries : 2;

function getClientIp(req: express.Request): string {
  const forwarded = req.headers["x-forwarded-for"];
  if (trustForwardedIp && typeof forwarded === "string" && forwarded.length > 0) {
    return forwarded.split(",")[0].trim();
  }
  return req.ip ?? req.socket.remoteAddress ?? "unknown";
}

function requestId(req: express.Request): string {
  const existing = req.header("x-request-id");
  return existing && existing.length > 0 ? existing : crypto.randomUUID();
}

function auditLog(event: string, payload: Record<string, unknown>): void {
  console.log(
    JSON.stringify({
      timestamp: new Date().toISOString(),
      category: "audit",
      event,
      ...payload
    })
  );
}

type ErrorCode =
  | "ERR_BAD_REQUEST"
  | "ERR_UNAUTHORIZED"
  | "ERR_RATE_LIMITED"
  | "ERR_NOT_FOUND"
  | "ERR_UPSTREAM_UNAVAILABLE"
  | "ERR_INTERNAL";

function respondWithError(
  res: express.Response,
  status: number,
  code: ErrorCode,
  message: string,
  details?: unknown
) {
  return res.status(status).json({ error: { code, message, details } });
}

function requireApiKey(keyName: "admin" | "gateway") {
  return (req: express.Request, res: express.Response, next: express.NextFunction): void => {
    if (!secureMode) return next();
    const expected = keyName === "admin" ? adminApiKey : gatewayApiKey;
    if (!expected) {
      return void res.status(500).json({ error: `${keyName.toUpperCase()} API key is not configured.` });
    }
    const provided = req.header("x-api-key") ?? "";
    if (provided !== expected) {
      incMetric("authFailures");
      auditLog("auth_failed", { scope: keyName, ip: getClientIp(req), path: req.path });
      return void res.status(401).json({ error: "Unauthorized" });
    }
    next();
  };
}

function rateLimit(prefix: string, max = defaultLimitMax, windowMs = defaultLimitWindowMs) {
  return (req: express.Request, res: express.Response, next: express.NextFunction): void => {
    const now = Date.now();
    const key = `${prefix}:${getClientIp(req)}`;
    const bucket = rateLimitStore.get(key);
    if (!bucket || now > bucket.resetAt) {
      rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
      return next();
    }
    if (bucket.count >= max) {
      incMetric("rateLimited");
      res.setHeader("Retry-After", String(Math.ceil((bucket.resetAt - now) / 1000)));
      auditLog("rate_limit_block", { scope: prefix, ip: getClientIp(req), path: req.path });
      return void res.status(429).json({ error: "Rate limit exceeded" });
    }
    bucket.count += 1;
    rateLimitStore.set(key, bucket);
    next();
  };
}
app.use((req, res, next) => {
  incMetric("requestsTotal");
  const rid = requestId(req);
  res.setHeader("x-request-id", rid);
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "no-referrer");
  res.setHeader("X-XSS-Protection", "1; mode=block");
  res.setHeader("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'");
  res.header("Access-Control-Allow-Origin", adminCorsOrigin);
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key, x-request-id");
  res.header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS");
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

const offeringsFilePath = path.resolve(process.cwd(), "data", "offerings.json");

type OfferingRecord = {
  id: string;
  title: string;
  description: string;
  pricing: string;
  tier: "starter" | "growth" | "scale";
  deliverables: string[];
  ctaLabel: string;
  ctaUrl: string;
  status: "live" | "new";
  order: number;
  archived: boolean;
  updatedAt: string;
};

const offeringSchema = z.object({
  title: z.string().min(3),
  description: z.string().min(10),
  pricing: z.string().min(3),
  tier: z.enum(["starter", "growth", "scale"]).default("starter"),
  deliverables: z.array(z.string().min(2)).min(1).default(["Initial delivery scope workshop"]),
  ctaLabel: z.string().min(2).default("Book discovery"),
  ctaUrl: z.string().url().default("https://example.com/book"),
  status: z.enum(["live", "new"])
});

const offeringUpdateSchema = z
  .object({
    title: z.string().min(3).optional(),
    description: z.string().min(10).optional(),
    pricing: z.string().min(3).optional(),
    tier: z.enum(["starter", "growth", "scale"]).optional(),
    deliverables: z.array(z.string().min(2)).min(1).optional(),
    ctaLabel: z.string().min(2).optional(),
    ctaUrl: z.string().url().optional(),
    status: z.enum(["live", "new"]).optional(),
    archived: z.boolean().optional()
  })
  .refine((obj) => Object.keys(obj).length > 0, { message: "At least one field must be provided" });

const offeringsReorderSchema = z.object({
  ids: z.array(z.string().min(1)).min(1)
});

function normalizeOfferings(items: unknown[]): OfferingRecord[] {
  return items
    .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    .map((item, index) => {
      const status: OfferingRecord["status"] = item.status === "live" ? "live" : "new";
      const tier: OfferingRecord["tier"] =
        item.tier === "growth" || item.tier === "scale" ? item.tier : "starter";
      return {
        id: String(item.id ?? `offering-${index + 1}`),
        title: String(item.title ?? "Untitled Offering"),
        description: String(item.description ?? ""),
        pricing: String(item.pricing ?? ""),
        tier,
        deliverables: Array.isArray(item.deliverables)
          ? item.deliverables.map((x) => String(x)).filter((x) => x.length > 0)
          : ["Initial delivery scope workshop"],
        ctaLabel: String(item.ctaLabel ?? "Book discovery"),
        ctaUrl: String(item.ctaUrl ?? "https://example.com/book"),
        status,
        order: Number.isFinite(Number(item.order)) ? Number(item.order) : index,
        archived: Boolean(item.archived ?? false),
        updatedAt: typeof item.updatedAt === "string" ? item.updatedAt : new Date().toISOString()
      };
    })
    .sort((a, b) => a.order - b.order)
    .map((item, index) => ({ ...item, order: index }));
}

async function ensureOfferingsFile(): Promise<void> {
  const initial = [
    {
      id: "video-repurposing-pipeline",
      title: "Video Repurposing Pipeline",
      description: "Input one YouTube/video URL, output ready-to-schedule short-form clips with hooks and platform copy.",
      pricing: "Typical offer: ~500 USD/month.",
      status: "live",
      order: 0,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "lead-enrichment-agent",
      title: "Lead Enrichment Agent",
      description: "Ingest raw company lists, enrich public web signals, score ICP fit, and route qualified leads to CRM.",
      pricing: "Use case: outbound teams and agencies.",
      status: "live",
      order: 1,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "competitive-intelligence-pipeline",
      title: "Competitive Intelligence Pipeline",
      description: "Scheduled competitor monitoring with diffs on pricing, features, hiring and messaging.",
      pricing: "Typical offer: 1,000-2,500 USD/month.",
      status: "live",
      order: 2,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "invoice-document-extraction",
      title: "Invoice & Document Extraction",
      description: "Extract structured fields from invoices, receipts, contracts and POs with schema validation.",
      pricing: "Pricing model: per-document or monthly package.",
      status: "live",
      order: 3,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "knowledge-base-support-automation",
      title: "Knowledge Base & Support Automation",
      description: "Detect documentation gaps from support tickets and auto-draft docs in your style.",
      pricing: "Typical model: setup fee + monthly retainer.",
      status: "live",
      order: 4,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "ai-compliance-monitoring-smb",
      title: "AI Compliance Monitoring for SMB",
      description: "Monitor regulatory changes and produce concrete action steps for small business teams.",
      pricing: "Typical offer: 300-500 USD/month.",
      status: "new",
      order: 5,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "ai-proposal-writing",
      title: "AI-Powered Proposal Writing",
      description: "Turn discovery notes into polished, branded proposals using prior proposal context.",
      pricing: "Pricing: 150-300 USD/month or ~50 USD/proposal.",
      status: "new",
      order: 6,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "ecommerce-listing-quality-control",
      title: "E-Commerce Listing Quality Control",
      description: "Audit full product catalogs, flag errors, fill missing attributes, and standardize SEO descriptions.",
      pricing: "Pricing: 500-2,000 USD per audit + retainer.",
      status: "new",
      order: 7,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "industry-specific-ai-training-packages",
      title: "Industry-Specific AI Training Packages",
      description: "Deploy verticalized AI setups with domain context, prompt libraries, and workflow templates.",
      pricing: "Pricing: 2,000-5,000 USD setup + 200-500 USD/month.",
      status: "new",
      order: 8,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "local-competitor-intelligence",
      title: "Local Competitor Intelligence",
      description: "Track local competitors across pricing, services, reviews and social activity with weekly briefs.",
      pricing: "Pricing: 200-400 USD/month.",
      status: "new",
      order: 9,
      archived: false,
      updatedAt: new Date().toISOString()
    },
    {
      id: "ai-workflow-auditing-service",
      title: "AI Workflow Auditing as a Service",
      description: "Audit AI workflows, identify quality gaps, and prioritize what to fix, standardize, or scale.",
      pricing: "Pricing: 1,500-3,000 USD per audit.",
      status: "new",
      order: 10,
      archived: false,
      updatedAt: new Date().toISOString()
    }
  ];

  try {
    await fs.access(offeringsFilePath);
  } catch {
    await fs.mkdir(path.dirname(offeringsFilePath), { recursive: true });
    await fs.writeFile(offeringsFilePath, JSON.stringify(initial, null, 2), "utf-8");
  }
}

async function readOfferings(): Promise<OfferingRecord[]> {
  await ensureOfferingsFile();
  const raw = await fs.readFile(offeringsFilePath, "utf-8");
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error("Invalid offerings file format.");
  }
  return normalizeOfferings(parsed);
}

async function writeOfferings(items: OfferingRecord[]): Promise<void> {
  await fs.writeFile(offeringsFilePath, JSON.stringify(normalizeOfferings(items), null, 2), "utf-8");
}

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

app.get("/metrics", (_req, res) => {
  res.json(getMetricsSnapshot());
});

app.get("/ready", async (_req, res) => {
  try {
    const response = await fetchWithRetry(
      `${integrationTargets.agents}/health`,
      { method: "GET" },
      { timeoutMs: downstreamTimeoutMs, retries: 1, retryDelayMs: 200 }
    );
    if (!response.ok) {
      return respondWithError(res, 503, "ERR_UPSTREAM_UNAVAILABLE", "Agents service is not ready.");
    }
    return res.json({ ok: true, service: "ai-ready-gateway", ready: true });
  } catch (error) {
    return respondWithError(
      res,
      503,
      "ERR_UPSTREAM_UNAVAILABLE",
      "Gateway readiness check failed.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.get("/admin", requireApiKey("admin"), (_req, res) => {
  res.sendFile(path.resolve(process.cwd(), "src/admin/index.html"));
});

app.get("/admin/offerings", requireApiKey("admin"), rateLimit("admin-offerings-read", 120), async (req, res) => {
  try {
    const offerings = await readOfferings();
    const includeArchived = String(req.query.includeArchived ?? "false").toLowerCase() === "true";
    res.json({ items: includeArchived ? offerings : offerings.filter((item) => !item.archived) });
  } catch (error) {
    return respondWithError(
      res,
      500,
      "ERR_INTERNAL",
      "Failed to read offerings.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.post("/admin/offerings", requireApiKey("admin"), rateLimit("admin-offerings-write", 60), async (req, res) => {
  const parsed = offeringSchema.safeParse(req.body);
  if (!parsed.success) {
    return respondWithError(res, 400, "ERR_BAD_REQUEST", "Invalid offering payload", parsed.error.flatten());
  }
  try {
    const offerings = await readOfferings();
    const id = parsed.data.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
    if (offerings.some((item) => item.id === id)) {
      return respondWithError(res, 409, "ERR_BAD_REQUEST", "Offering with this title already exists.");
    }
    const next: OfferingRecord = {
      id,
      ...parsed.data,
      order: offerings.length,
      archived: false,
      updatedAt: new Date().toISOString()
    };
    offerings.push(next);
    await writeOfferings(offerings);
    auditLog("offering_created", {
      requestId: requestId(req),
      offeringId: id,
      ip: getClientIp(req)
    });
    res.status(201).json(next);
  } catch (error) {
    return respondWithError(
      res,
      500,
      "ERR_INTERNAL",
      "Failed to create offering.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.put("/admin/offerings/:id", requireApiKey("admin"), rateLimit("admin-offerings-write", 60), async (req, res) => {
  const parsed = offeringUpdateSchema.safeParse(req.body);
  if (!parsed.success) {
    return respondWithError(res, 400, "ERR_BAD_REQUEST", "Invalid update payload", parsed.error.flatten());
  }
  try {
    const offerings = await readOfferings();
    const index = offerings.findIndex((item) => item.id === req.params.id);
    if (index < 0) {
      return respondWithError(res, 404, "ERR_NOT_FOUND", "Offering not found.");
    }
    const updated = { ...offerings[index], ...parsed.data, updatedAt: new Date().toISOString() };
    offerings[index] = updated;
    await writeOfferings(offerings);
    auditLog("offering_updated", {
      requestId: requestId(req),
      offeringId: updated.id,
      ip: getClientIp(req)
    });
    res.json(updated);
  } catch (error) {
    return respondWithError(
      res,
      500,
      "ERR_INTERNAL",
      "Failed to update offering.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.delete("/admin/offerings/:id", requireApiKey("admin"), rateLimit("admin-offerings-write", 60), async (req, res) => {
  try {
    const offerings = await readOfferings();
    const index = offerings.findIndex((item) => item.id === req.params.id);
    if (index < 0) {
      return respondWithError(res, 404, "ERR_NOT_FOUND", "Offering not found.");
    }
    if (offerings[index].archived) {
      return respondWithError(res, 409, "ERR_BAD_REQUEST", "Offering is already archived.");
    }
    offerings[index] = { ...offerings[index], archived: true, updatedAt: new Date().toISOString() };
    await writeOfferings(offerings);
    auditLog("offering_archived", {
      requestId: requestId(req),
      offeringId: offerings[index].id,
      ip: getClientIp(req)
    });
    res.status(200).json(offerings[index]);
  } catch (error) {
    return respondWithError(
      res,
      500,
      "ERR_INTERNAL",
      "Failed to delete offering.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.post("/admin/offerings/reorder", requireApiKey("admin"), rateLimit("admin-offerings-write", 60), async (req, res) => {
  const parsed = offeringsReorderSchema.safeParse(req.body);
  if (!parsed.success) {
    return respondWithError(res, 400, "ERR_BAD_REQUEST", "Invalid reorder payload", parsed.error.flatten());
  }
  try {
    const offerings = await readOfferings();
    const active = offerings.filter((item) => !item.archived);
    const activeIds = new Set(active.map((item) => item.id));
    const allIds = new Set(offerings.map((item) => item.id));
    const payloadIds = parsed.data.ids;
    const fullReorder = payloadIds.length === offerings.length && payloadIds.every((id) => allIds.has(id));
    const activeOnlyReorder = payloadIds.length === active.length && payloadIds.every((id) => activeIds.has(id));
    if (!fullReorder && !activeOnlyReorder) {
      return respondWithError(
        res,
        400,
        "ERR_BAD_REQUEST",
        "Reorder payload must include all ids or all non-archived ids exactly once."
      );
    }

    const byId = new Map(offerings.map((item) => [item.id, item]));
    const now = new Date().toISOString();
    let reordered: OfferingRecord[] = [];
    if (fullReorder) {
      reordered = payloadIds.map((id, index) => {
        const item = byId.get(id)!;
        return { ...item, order: index, updatedAt: now };
      });
    } else {
      const reorderedActive = payloadIds.map((id, index) => {
        const item = byId.get(id)!;
        return { ...item, order: index, updatedAt: now };
      });
      const archived = offerings
        .filter((item) => item.archived)
        .sort((a, b) => a.order - b.order)
        .map((item, index) => ({ ...item, order: reorderedActive.length + index }));
      reordered = [...reorderedActive, ...archived];
    }
    await writeOfferings(reordered);
    auditLog("offerings_reordered", {
      requestId: requestId(req),
      ids: parsed.data.ids,
      ip: getClientIp(req)
    });
    res.json({ items: reordered });
  } catch (error) {
    return respondWithError(
      res,
      500,
      "ERR_INTERNAL",
      "Failed to reorder offerings.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.get("/admin/integrations/health", requireApiKey("admin"), rateLimit("admin-health", 60), async (_req, res) => {
  const checks = await Promise.all(
    Object.entries(integrationTargets).map(async ([name, base]) => {
      const healthUrl = name === "n8n" ? `${base}/healthz` : `${base}/health`;
      const started = Date.now();
      try {
        const response = await fetchWithRetry(
          healthUrl,
          { method: "GET" },
          { timeoutMs: downstreamTimeoutMs, retries: 1, retryDelayMs: 200 }
        );
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

app.post("/admin/actions/run", requireApiKey("admin"), rateLimit("admin-actions", 50), async (req, res) => {
  const parsed = actionSchema.safeParse(req.body);
  if (!parsed.success) {
    return respondWithError(res, 400, "ERR_BAD_REQUEST", "Invalid action body", parsed.error.flatten());
  }

  const payload = parsed.data.payload ?? {};
  try {
    if (parsed.data.action === "runInbox") {
      const response = await fetchWithRetry(
        `${integrationTargets.agents}/agents/inbox/run`,
        {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-service-key": process.env.SERVICE_SHARED_KEY ?? "" },
        body: JSON.stringify({ email_limit: 10, ...payload })
        },
        { timeoutMs: downstreamTimeoutMs, retries: downstreamRetries, retryDelayMs: 400 }
      );
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runCrm") {
      const response = await fetchWithRetry(
        `${integrationTargets.agents}/agents/crm/run`,
        {
        method: "POST",
        headers: { "x-service-key": process.env.SERVICE_SHARED_KEY ?? "" }
        },
        { timeoutMs: downstreamTimeoutMs, retries: downstreamRetries, retryDelayMs: 400 }
      );
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runMarketing") {
      const response = await fetchWithRetry(
        `${integrationTargets.agents}/agents/marketing/run`,
        {
        method: "POST",
        headers: { "x-service-key": process.env.SERVICE_SHARED_KEY ?? "" }
        },
        { timeoutMs: downstreamTimeoutMs, retries: downstreamRetries, retryDelayMs: 400 }
      );
      return res.status(response.status).json(await response.json());
    }
    if (parsed.data.action === "runDelivery") {
      const response = await fetchWithRetry(
        `${integrationTargets.agents}/agents/delivery/run`,
        {
        method: "POST",
        headers: { "x-service-key": process.env.SERVICE_SHARED_KEY ?? "" }
        },
        { timeoutMs: downstreamTimeoutMs, retries: downstreamRetries, retryDelayMs: 400 }
      );
      return res.status(response.status).json(await response.json());
    }

    const councilPayload = {
      question: "Give a concise executive summary of current AI operations posture.",
      context: { source: "gateway-admin-ui", timestamp: new Date().toISOString() }
    };
    const councilResponse = await fetchWithRetry(
      `${integrationTargets.council}/council/decide`,
      {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-service-key": process.env.SERVICE_SHARED_KEY ?? ""
      },
      body: JSON.stringify(councilPayload)
      },
      { timeoutMs: downstreamTimeoutMs, retries: downstreamRetries, retryDelayMs: 400 }
    );
    return res.status(councilResponse.status).json(await councilResponse.json());
  } catch (error) {
    return respondWithError(
      res,
      502,
      "ERR_UPSTREAM_UNAVAILABLE",
      "Action execution failed.",
      error instanceof Error ? error.message : "Unknown error"
    );
  }
});

app.post("/v1/chat/completions", requireApiKey("gateway"), rateLimit("chat-completions"), async (req, res) => {
  const parsed = requestSchema.safeParse(req.body);
  if (!parsed.success) {
    return respondWithError(res, 400, "ERR_BAD_REQUEST", "Invalid request body", parsed.error.flatten());
  }

  const models = loadModelsConfig();
  const modelCfg = models[parsed.data.model];
  if (!modelCfg) {
    return respondWithError(res, 404, "ERR_NOT_FOUND", `Unknown model alias: ${parsed.data.model}`);
  }

  const started = Date.now();
  const rid = requestId(req);
  incMetric("chatCompletionsTotal");
  try {
    const provider = resolveProvider(modelCfg.provider);
    const response = await provider.complete(parsed.data, modelCfg);

    logRequest({
      requestId: rid,
      alias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started,
      usage: response.usage
    });
    auditLog("gateway_completion_success", {
      requestId: rid,
      modelAlias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started,
      ip: getClientIp(req)
    });

    return res.json({
      ...response,
      model: parsed.data.model
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown gateway error.";
    incMetric("chatCompletionsFailed");
    logRequest({
      alias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started
    });
    auditLog("gateway_completion_failed", {
      requestId: rid,
      modelAlias: parsed.data.model,
      provider: modelCfg.provider,
      latencyMs: Date.now() - started,
      ip: getClientIp(req),
      error: message
    });
    return respondWithError(res, 502, "ERR_UPSTREAM_UNAVAILABLE", message);
  }
});

const port = Number(process.env.PORT ?? 4000);
app.listen(port, () => {
  console.log(`Gateway listening on http://localhost:${port}`);
});
