# AI Ready Backend Infrastructure

This repository contains the backend and AI infrastructure stack for AI Ready.

## Services

- `gateway/`: TypeScript LLM gateway with provider abstraction and alias routing.
- `agents/`: Python LangGraph/Hermes agents and HTTP surfaces.
- `data/`: Python data layer, ETL jobs, and storage integration code.
- `orchestrator/`: n8n and related orchestration runtime configuration.
- `governance/`: LLM Council and Paperclip integration layers.
- `local-models/`: Local model runtimes and wrappers (Gemma, llm.c).

## Current Status

Phase 0 and Phase 1 are scaffolded and the gateway is implemented.
