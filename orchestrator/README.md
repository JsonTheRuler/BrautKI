# Orchestrator

This folder contains n8n orchestration for connecting triggers (email, webhooks, CRM) to AI agents.

## Services

- `docker-compose.yml`: runs `n8n` + dedicated `postgres` for n8n state.
- `.env.example`: environment defaults.

## Start n8n

```bash
cd orchestrator
cp .env.example .env
docker compose up -d
```

Open n8n at:
- `http://localhost:5678`

## Workflow 1: Email triage (documented + export)

Import:
- `workflows/email-triage-workflow.json`

### Node-by-node

1. **Webhook Trigger**
   - Path: `email-triage`
   - Method: `POST`
2. **Run Inbox Agent** (`HTTP Request`)
   - URL: `http://host.docker.internal:8010/agents/inbox/run`
   - Body JSON:
     ```json
     { "email_limit": 10 }
     ```
3. **Format Triage Summary** (`Code`)
   - Converts response to compact summary (`triage_count`, `triage`)
4. **Respond to Webhook**
   - Returns JSON payload to caller.

### Triggering the workflow

```bash
curl -X POST http://localhost:5678/webhook/email-triage
```

Expected result: triage array with draft replies from the Inbox agent.

## Workflow 2: AI-readiness lead pipeline (blueprint)

Use this node chain in n8n:

1. **Webhook Trigger** (`POST /ai-readiness-lead`)
   - receives website form payload
2. **Postgres Node** (or HTTP call to data API)
   - insert into `leads`
3. **HTTP Request**
   - `POST http://host.docker.internal:8010/agents/crm/run`
4. **Notification Node** (Slack/Teams/Email)
   - send summary with lead details + score + suggested outreach

Suggested payload passed from trigger:

```json
{
  "company_name": "Example AS",
  "contact_name": "Jane Doe",
  "contact_email": "jane@example.no",
  "source": "website_ai_check",
  "metadata": {
    "maturity_score": 58,
    "team_size": 45
  }
}
```

This second workflow is intentionally documented first and can be exported once Phase 3 CRM implementation is completed.
