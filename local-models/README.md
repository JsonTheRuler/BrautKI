# Local Models

Runtime scripts and wrappers for local Gemma and Karpathy llm.c models.

## Overview

This folder provides:

- `ollama` runtime for local Gemma.
- `gemma-openai-wrapper` exposing OpenAI-compatible `/v1/chat/completions`.
- `karpathy-wrapper` exposing OpenAI-compatible `/v1/chat/completions` for llm.c-style usage.

## Files

- `docker-compose.yml`: launches Ollama + both wrappers.
- `Dockerfile.wrapper`: shared wrapper image.
- `src/local_models/wrapper_api.py`: wrapper HTTP API.

## Start local runtimes

```bash
cd local-models
docker compose up -d --build
```

Pull Gemma model in Ollama (first run):

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama pull gemma3:27b
```

## Endpoints

- Gemma wrapper: `http://localhost:11500/v1/chat/completions`
- Karpathy wrapper: `http://localhost:11600/v1/chat/completions`
- Ollama native: `http://localhost:11434`

## Gateway wiring

`gateway/models.yml` aliases:

- `internal-secure` -> local Gemma (through local-http provider)
- Default local model name: `gemma3:27b`
- `karpathy-eval` -> Karpathy wrapper

Set in `gateway/.env`:

- `LOCAL_GEMMA_BASE_URL=http://localhost:11500`
- `KARPATHY_BASE_URL=http://localhost:11600`

## Delivery agent sensitive flow

The Delivery agent uses:
- `INTERNAL_SECURE_MODEL_ALIAS=internal-secure`

for drafting sensitive internal readiness reports.

## Karpathy llm.c integration note

`karpathy-wrapper` supports optional shell-out to llm.c runner via:

- `KARPATHY_BINARY_PATH`
- `KARPATHY_MODEL_PATH`

If those are missing, it returns a deterministic style-normalizer fallback so the interface remains testable.
