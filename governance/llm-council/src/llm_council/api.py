from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Response

from .observability import log_event, metrics
from .schemas import CouncilRequest
from .service import as_openai_style_response, council_decide

app = FastAPI(title="AI Ready LLM Council", version="0.1.0")
service_shared_key = os.getenv("SERVICE_SHARED_KEY", "")
secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"


def enforce_service_key(x_service_key: str) -> None:
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
def metrics_endpoint() -> dict:
    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "counters": {
            "requestsTotal": metrics.requests_total,
            "authFailures": metrics.auth_failures,
            "councilDecisions": metrics.council_decisions,
        },
    }


@app.post("/council/decide")
def decide(payload: dict[str, Any], x_service_key: str = Header(default="")) -> dict[str, Any]:
    enforce_service_key(x_service_key)
    metrics.council_decisions += 1
    """
    Supports two shapes:
    1) Native council: {question, context}
    2) Gateway forwarded chat payload: {model, messages, ...}
    """
    if "question" in payload:
        req = CouncilRequest.model_validate(payload)
        result = council_decide(req)
        return result.model_dump()

    if "messages" in payload:
        messages = payload.get("messages", [])
        combined = "\n".join(msg.get("content", "") for msg in messages if isinstance(msg, dict))
        req = CouncilRequest(
            question="Council review request",
            context={"messages": messages, "combined_prompt": combined},
        )
        result = council_decide(req)
        requested_model = payload.get("model", "council-meta")
        return as_openai_style_response(result, requested_model=requested_model)

    raise HTTPException(status_code=400, detail="Unsupported payload. Provide {question, context} or chat messages.")


def main() -> None:
    uvicorn.run("llm_council.api:app", host="0.0.0.0", port=8088, reload=False)


if __name__ == "__main__":
    main()
