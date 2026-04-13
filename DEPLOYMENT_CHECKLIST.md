# Deployment Checklist

Use this checklist before each production rollout.

## 1) Infrastructure readiness

- [ ] Docker is running on host machine.
- [ ] Required services are healthy:
  - [ ] Gateway (`/health`)
  - [ ] Agents API (`/health`)
  - [ ] LLM Council (`/health`)
  - [ ] n8n (`/healthz`)
  - [ ] Local model wrappers (`/health`)
- [ ] Environment variables are set (`.env` files present, no missing API keys).

## 2) Gateway verification

- [ ] `POST /v1/chat/completions` works with:
  - [ ] `reasoning-primary`
  - [ ] `fast-cheap`
  - [ ] `council-meta`
  - [ ] `karpathy-eval`
- [ ] `internal-secure` responds (or model download status is known).
- [ ] Admin UI is reachable at `/admin`.

## 3) Data layer verification

- [ ] Postgres reachable from `data` package.
- [ ] `data/migrations/0001_init.sql` applied.
- [ ] `etl_emails.py` can run and insert records.

## 4) Agent workflows

- [ ] Inbox agent endpoint returns structured output.
- [ ] Draft reply persistence path is writable.
- [ ] Delivery agent can run with/without council review.

## 5) Orchestration and governance

- [ ] n8n email triage workflow import is valid.
- [ ] Paperclip daily standup workflow runs and produces summary.
- [ ] Slack/email webhook notifications (if used) succeed.

## 6) Release controls

- [ ] All tests and smoke checks pass.
- [ ] Changelog / release notes updated.
- [ ] Git tag created for release.
- [ ] Rollback plan documented (previous tag + restore steps).
