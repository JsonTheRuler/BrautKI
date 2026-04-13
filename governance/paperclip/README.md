# Paperclip

Paperclip org-layer configuration and workflows for AI Ready.

## AI org chart (roles -> agent endpoints)

Configured in:
- `paperclip-org.yaml`

Company:
- `AI Ready`

Roles:
- CEO agent -> `POST /agents/inbox/run`
- Sales agent -> `POST /agents/crm/run`
- Ops agent -> `POST /agents/inbox/run`
- Marketing agent -> `POST /agents/marketing/run`
- Delivery agent -> `POST /agents/delivery/run`

Each role includes task types and optional payload templates.

## Paperclip runtime config

`docker-compose.yml` includes a Paperclip service mounting `paperclip-org.yaml`.

```bash
cd governance/paperclip
docker compose up -d
```

## Daily standup workflow

Implemented in:
- `src/paperclip_workflows/daily_standup.py`

Behavior:
1. Loads role registry from `paperclip-org.yaml`.
2. Calls each role endpoint every run.
3. Collects each role's output (`did`, `blockers`, `plan` equivalent in role output payload).
4. Aggregates a markdown summary.
5. Sends summary to Slack and/or Email webhook if configured.

### Run daily standup manually

```bash
cd governance/paperclip
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
paperclip-daily-standup
```

### Notification config

Optional environment variables:
- `STANDUP_SLACK_WEBHOOK_URL`
- `STANDUP_EMAIL_WEBHOOK_URL`
- `STANDUP_EMAIL_RECIPIENTS` (comma-separated)

### Suggested schedule

Use Paperclip scheduler or external cron:
- `0 8 * * 1-5` (weekdays at 08:00 local time)
