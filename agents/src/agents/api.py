from __future__ import annotations

import os
import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Response

from agents.graphs.crm_agent import run_crm_agent
from agents.graphs.delivery_agent import run_delivery_agent
from agents.graphs.inbox_agent import run_inbox_agent
from agents.graphs.marketing_agent import run_marketing_agent
from agents.observability import log_event, metrics
from agents.schemas import (
    CrmAgentResponse,
    DeliveryAgentResponse,
    InboxAgentRequest,
    InboxAgentResponse,
    MarketingAgentResponse,
)

app = FastAPI(title="AI Ready Agents API", version="0.1.0")
service_shared_key = os.getenv("SERVICE_SHARED_KEY", "")
secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"


def enforce_service_key(x_service_key: str = Header(default="")) -> None:
    if not secure_mode:
        return
    if not service_shared_key:
        raise HTTPException(status_code=500, detail="SERVICE_SHARED_KEY is not configured")
    if x_service_key != service_shared_key:
        metrics.auth_failures += 1
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    metrics.requests_total += 1
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    response: Response = await call_next(request)
    response.headers["x-request-id"] = rid
    log_event("request", {"requestId": rid, "path": request.url.path, "status": response.status_code})
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, bool]:
    return {"ready": True}


@app.get("/metrics")
def metrics_endpoint(x_service_key: str = Header(default="")) -> dict:
    enforce_service_key(x_service_key)
    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "counters": {
            "requestsTotal": metrics.requests_total,
            "authFailures": metrics.auth_failures,
            "inboxRuns": metrics.inbox_runs,
            "crmRuns": metrics.crm_runs,
            "marketingRuns": metrics.marketing_runs,
            "deliveryRuns": metrics.delivery_runs,
        },
    }


@app.post("/agents/inbox/run", response_model=InboxAgentResponse)
def run_inbox(request: InboxAgentRequest, x_service_key: str = Header(default="")) -> InboxAgentResponse:
    enforce_service_key(x_service_key)
    metrics.inbox_runs += 1
    result = run_inbox_agent(email_limit=request.email_limit)
    return InboxAgentResponse(result=result)


@app.post("/agents/crm/run", response_model=CrmAgentResponse)
def run_crm(x_service_key: str = Header(default="")) -> CrmAgentResponse:
    enforce_service_key(x_service_key)
    metrics.crm_runs += 1
    try:
        output = run_crm_agent()
    except Exception as exc:
        log_event("agent_error", {"agent": "crm", "error": str(exc)})
        raise HTTPException(status_code=500, detail="CRM agent execution failed") from exc
    return CrmAgentResponse(status="completed", output=output)


@app.post("/agents/marketing/run", response_model=MarketingAgentResponse)
def run_marketing(x_service_key: str = Header(default="")) -> MarketingAgentResponse:
    enforce_service_key(x_service_key)
    metrics.marketing_runs += 1
    try:
        output = run_marketing_agent()
    except Exception as exc:
        log_event("agent_error", {"agent": "marketing", "error": str(exc)})
        raise HTTPException(status_code=500, detail="Marketing agent execution failed") from exc
    return MarketingAgentResponse(status="completed", output=output)


@app.post("/agents/delivery/run", response_model=DeliveryAgentResponse)
def run_delivery(x_service_key: str = Header(default="")) -> DeliveryAgentResponse:
    enforce_service_key(x_service_key)
    metrics.delivery_runs += 1
    try:
        output = run_delivery_agent()
    except Exception as exc:
        log_event("agent_error", {"agent": "delivery", "error": str(exc)})
        raise HTTPException(status_code=500, detail="Delivery agent execution failed") from exc
    return DeliveryAgentResponse(status="completed", output=output)


def main() -> None:
    uvicorn.run("agents.api:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
