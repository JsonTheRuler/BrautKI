# Observability

This folder contains baseline observability artifacts:

- `dashboard-template.json`: metric panels to implement in your monitoring tool.
- `alerts-template.md`: starter alert conditions and triage checklist.

## Runtime metrics endpoints

- Gateway: `GET /metrics`
- Agents: `GET /metrics`
- Council: `GET /metrics`

## Runtime logging

- Gateway emits structured request + audit logs.
- Agents and council emit structured request logs with `x-request-id`.
