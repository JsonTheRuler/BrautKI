# Agents

Python LangGraph/FastAPI services for AI Ready.

## Implemented through Batch 5

- Inbox agent implemented end-to-end as a LangGraph workflow.
- CRM agent implemented with lead enrichment + ICP scoring contract.
- Marketing agent implemented with channel draft generation contract.
- Delivery agent implemented with validated draft report + optional council review.
- HTTP API supports all agents for n8n/Paperclip orchestration.

## Project layout

- `src/agents/graphs/inbox_agent.py` - working Inbox graph.
- `src/agents/graphs/crm_agent.py` - CRM workflow (fetch -> enrich/score -> format/validate).
- `src/agents/graphs/marketing_agent.py` - Marketing workflow (assets -> draft generation -> validate).
- `src/agents/graphs/delivery_agent.py` - Delivery workflow (inputs -> draft -> optional council review).
- `src/agents/tools/inbox_tools.py` - `get_recent_emails`, `get_calendar_events`, `save_draft_reply`.
- `src/agents/gateway_client.py` - all LLM calls routed through gateway.
- `src/agents/api.py` - FastAPI endpoints.
- `src/agents/scripts/test_inbox_agent.py` - Inbox endpoint smoke test.

## Environment

Set these variables before running:

- `GATEWAY_URL=http://localhost:4000`
- `SECURE_MODE=false`
- `SERVICE_SHARED_KEY=` (required when `SECURE_MODE=true`)
- `REASONING_MODEL_ALIAS=reasoning-primary`
- `COUNCIL_MODEL_ALIAS=council-meta`
- `ENABLE_COUNCIL_REVIEW=false`
- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_ready`
- `DRAFTS_OUTPUT_PATH=runtime/draft_replies.jsonl`
- `CALENDAR_STUB_PATH=` (optional path to JSON calendar fixture)

## Install and run

```bash
cd agents
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
agents-api
```

API base: `http://localhost:8010`

- `GET /health`
- `GET /ready`
- `POST /agents/inbox/run`
- `POST /agents/crm/run`
- `POST /agents/marketing/run`
- `POST /agents/delivery/run`

## Inbox agent test

In another terminal:

```bash
cd agents
. .venv/Scripts/activate
inbox-agent-test
```

Or curl:

```bash
curl -X POST http://localhost:8010/agents/inbox/run \
  -H "Content-Type: application/json" \
  -d '{"email_limit":5}'
```

## How the Inbox agent works

LangGraph nodes:

1. `fetch_context`:
   - reads recent emails from Postgres (`emails` table) via `get_recent_emails()`
   - reads calendar events via `get_calendar_events()`
2. `llm_triage`:
   - calls gateway endpoint `POST /v1/chat/completions` through `gateway_client.py`
3. `format_output`:
   - validates output with Pydantic (`InboxAgentOutput`)
   - persists draft replies via `save_draft_reply()`

All LLM model calls go through the gateway alias defined by `REASONING_MODEL_ALIAS`.

## Core agent test (Batch 5)

```bash
cd agents
. .venv/Scripts/activate
core-agents-test
```

This validates CRM/Marketing/Delivery output contracts and fallback behavior.
