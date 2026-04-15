# Alert Template (Baseline)

## Critical

- Gateway readiness fails for 3 consecutive checks (1 min interval)
- Gateway `chatCompletionsFailed / chatCompletionsTotal` > 20% over 5 minutes
- Gateway auth failures > 50 in 5 minutes

## Warning

- Agents readiness fails for 2 consecutive checks
- Council readiness fails for 2 consecutive checks
- Gateway rate-limited responses > 30 in 5 minutes

## Investigation checklist

1. Check `health` and `ready` endpoints.
2. Inspect `audit` log events:
   - `auth_failed`
   - `rate_limit_block`
   - `gateway_completion_failed`
3. Verify env-key consistency:
   - `SERVICE_SHARED_KEY`
   - `ADMIN_API_KEY`
   - `GATEWAY_API_KEY`
4. Check upstream provider availability and latency.
