# Operations Runbook

## Purpose

Baseline incident and operational guide for AI Ready backend services.

## Services and health endpoints

- Gateway: `GET /health`, readiness: `GET /ready`
- Agents API: `GET /health`, readiness: `GET /ready`
- LLM Council: `GET /health`, readiness: `GET /ready`
- n8n: `GET /healthz`

## Common incidents

### 1) Elevated 502 errors on gateway chat endpoint

Checks:
- Confirm provider API keys are present.
- Confirm downstream timeout/retry settings:
  - `DOWNSTREAM_TIMEOUT_MS`
  - `DOWNSTREAM_RETRIES`
- Inspect audit logs for `gateway_completion_failed`.

Mitigation:
- Temporarily switch traffic to `fast-cheap`.
- Reduce timeout if request queue backs up.
- Disable problematic alias in `models.yml` until provider recovers.

### 2) Admin actions failing

Checks:
- `SECURE_MODE`, `ADMIN_API_KEY`, `SERVICE_SHARED_KEY` configured consistently.
- Agents/Council reachable from gateway base URLs.
- Audit logs for `auth_failed` or `rate_limit_block`.

Mitigation:
- Re-sync shared keys between services.
- Increase `RATE_LIMIT_MAX` temporarily if legitimate traffic burst.

### 3) Local model alias unavailable

Checks:
- Wrapper health:
  - `http://localhost:11500/health`
  - `http://localhost:11600/health`
- Ollama model pulled and loaded.

Mitigation:
- Route sensitive flow temporarily to cloud alias if policy allows.
- Keep wrappers up while model warm-up completes.

## Recovery procedure

1. Validate `health` and `ready` endpoints.
2. Tail service logs and filter for audit events and failures.
3. Restart only affected service.
4. Re-run smoke calls:
   - gateway `/v1/chat/completions`
   - admin action `runInbox`
5. Confirm error rate normalizes.

## Pre-deploy checks

- `npm run build` (gateway)
- `python -m compileall src` (agents, council)
- verify `.env` parity against required keys
