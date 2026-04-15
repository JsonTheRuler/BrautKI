# Production Readiness (Batch 7)

This file is the final production hardening reference for environments, secrets, and deployment workflow.

## 1) Environment and secrets matrix

Use the new `.env.example` files as canonical templates:

- `gateway/.env.example`
- `agents/.env.example`
- `data/.env.example`
- `governance/llm-council/.env.example`
- `local-models/.env.example`

Mandatory production secrets:

- Gateway:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `OPENROUTER_API_KEY`
  - `ADMIN_API_KEY` (if `SECURE_MODE=true`)
  - `GATEWAY_API_KEY` (if `SECURE_MODE=true`)
  - `SERVICE_SHARED_KEY` (if `SECURE_MODE=true`)
- Agents:
  - `SERVICE_SHARED_KEY` (if `SECURE_MODE=true`)
  - `DATABASE_URL`
- Data:
  - `DATABASE_URL`
  - Connector credentials if `EMAIL_SOURCE=imap|graph`
- Council:
  - `SERVICE_SHARED_KEY` (if `SECURE_MODE=true`)

## 2) Preflight validation

Run before every deploy:

```bash
python scripts/env_preflight.py --service all
python scripts/release_smoke.py
```

## 3) Vercel workflow (test-first)

Recommended branch model:

1. Create feature branch from `main`
2. Push branch to GitHub
3. Let Vercel create Preview deployment
4. Validate preview routes:
   - `/health`
   - `/ready`
   - `/admin` (with API key if secure mode)
5. Merge to `main` only after CI + preview checks pass

Use separate Vercel environment variable sets:

- Preview: test keys / sandbox credentials
- Production: real keys only

Never share `SERVICE_SHARED_KEY` between preview and production.

## 4) Promotion gate

Promote to production only when:

- CI checks pass (`.github/workflows/ci.yml`)
- `python scripts/release_smoke.py` passes locally
- `/metrics` and `/ready` are healthy for all required services
- rollback tag and runbook are prepared
