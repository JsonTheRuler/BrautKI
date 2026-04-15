# BrautKI

This repository contains the backend and AI infrastructure stack for AI Ready.

## Services

- `gateway/`: TypeScript LLM gateway with provider abstraction and alias routing.
- `agents/`: Python LangGraph/Hermes agents and HTTP surfaces.
- `data/`: Python data layer, ETL jobs, and storage integration code.
- `orchestrator/`: n8n and related orchestration runtime configuration.
- `governance/`: LLM Council and Paperclip integration layers.
- `local-models/`: Local model runtimes and wrappers (Gemma, llm.c).

## Batch 6: Release Controls

- Added CI pipeline in `.github/workflows/ci.yml`:
  - `gateway-build`: Node install + TypeScript build
  - `python-services`: agents/data/council compile + agent contract tests
- Added local release smoke runner: `scripts/release_smoke.py`
- Updated `DEPLOYMENT_CHECKLIST.md` with explicit CI and release smoke verification steps.

## Batch 7: Final Production Readiness

- Added env templates for all major services (`agents`, `data`, `llm-council`, `local-models`).
- Added env preflight validator: `scripts/env_preflight.py`.
- Added final ops guide: `PRODUCTION_READY.md` (secrets matrix + Vercel test/prod workflow).
