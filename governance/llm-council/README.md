# LLM Council

Wrapper service for council-style multi-model decisions.

## Endpoint

- `POST /council/decide`
  - Native payload: `{ "question": "...", "context": {...} }`
  - Returns: `{ final_answer, rationale, votes[] }`

The same endpoint also accepts chat-style payloads forwarded from the gateway alias `council-meta`.

## Setup

```bash
cd governance/llm-council
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
```

## Run

```bash
set GATEWAY_URL=http://localhost:4000
set COUNCIL_MEMBER_ALIASES=reasoning-primary,fast-cheap,internal-secure
set COUNCIL_SYNTHESIS_ALIAS=reasoning-primary
set SECURE_MODE=false
set SERVICE_SHARED_KEY=
llm-council-api
```

Default port: `8088`

Health/readiness:
- `GET /health`
- `GET /ready`

## Direct test

```bash
curl -X POST http://localhost:8088/council/decide \
  -H "Content-Type: application/json" \
  -H "x-service-key: <SERVICE_SHARED_KEY_IF_ENABLED>" \
  -d "{\"question\":\"Should we proceed with this AI delivery plan?\",\"context\":{\"industry\":\"logistics\",\"risk\":\"medium\"}}"
```

## Via gateway alias

Ensure `gateway/models.yml` contains:
- `council-meta -> provider: local-http, baseUrl: ${COUNCIL_BASE_URL}, path: /council/decide`

Then run:

```bash
python examples/call_council_via_gateway.py
```
