# Gateway

TypeScript LLM gateway exposing an OpenAI-compatible endpoint while routing by model alias.

## What it provides

- `POST /v1/chat/completions`
- Alias routing from `models.yml`
- Provider adapters:
  - OpenAI
  - Anthropic
  - OpenRouter
  - Local HTTP
- Basic JSON logging with timestamp, alias, provider, latency, and usage.

## 1) Setup

```bash
cd gateway
npm install
cp .env.example .env
```

Add API keys in `.env`:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`

Security flags:

- `SECURE_MODE=true` to enforce API-key auth and route rate-limits
- `GATEWAY_API_KEY=<key>` for `/v1/chat/completions`
- `ADMIN_API_KEY=<key>` for `/admin` + `/admin/*` APIs
- `SERVICE_SHARED_KEY=<key>` used when gateway calls agents/council services
- `DOWNSTREAM_TIMEOUT_MS=20000` timeout for downstream service calls
- `DOWNSTREAM_RETRIES=2` retry attempts for transient failures

## 2) Run

```bash
npm run dev
```

Health check:

```bash
curl http://localhost:4000/health
```

Readiness check:

```bash
curl http://localhost:4000/ready
```

## 3) Call the gateway

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: <GATEWAY_API_KEY_IF_SECURE_MODE>" \
  -d '{
    "model": "reasoning-primary",
    "messages": [{"role":"user","content":"Give me a 2-line AI operations summary."}],
    "temperature": 0.2,
    "max_tokens": 120
  }'
```

Try another alias:

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: <GATEWAY_API_KEY_IF_SECURE_MODE>" \
  -d '{
    "model": "fast-cheap",
    "messages": [{"role":"user","content":"Give me two bullet points on automation."}]
  }'
```

## 4) Smoke test script

```bash
npm run smoke:test
```

This sends one request to `reasoning-primary` and one to `fast-cheap`.

## 5) Admin console (ops UI)

The gateway now serves a lightweight admin page:

- URL: `http://localhost:4000/admin`
- Header when secure mode enabled: `x-api-key: <ADMIN_API_KEY>`

It provides:
- integration health checks (gateway, agents, council, n8n, local model wrappers)
- one-click action triggers for key agent and council flows

Optional integration env vars:
- `AGENTS_BASE_URL` (default `http://localhost:8010`)
- `COUNCIL_BASE_URL` (default `http://localhost:8088`)
- `N8N_BASE_URL` (default `http://localhost:5678`)
- `LOCAL_GEMMA_BASE_URL` (default `http://localhost:11500`)
- `KARPATHY_BASE_URL` (default `http://localhost:11600`)
