from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from agents.graphs.crm_agent import build_crm_graph
from agents.graphs.delivery_agent import build_delivery_graph
from agents.graphs.inbox_agent import run_inbox_agent
from agents.graphs.marketing_agent import build_marketing_graph
from agents.schemas import InboxAgentRequest, InboxAgentResponse

app = FastAPI(title="AI Ready Agents API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agents/inbox/run", response_model=InboxAgentResponse)
def run_inbox(request: InboxAgentRequest) -> InboxAgentResponse:
    result = run_inbox_agent(email_limit=request.email_limit)
    return InboxAgentResponse(result=result)


@app.post("/agents/crm/run")
def run_crm() -> dict:
    # Skeleton endpoint for phase progress visibility.
    state = build_crm_graph().invoke({})
    return {"status": "skeleton", "output": state.get("output", {})}


@app.post("/agents/marketing/run")
def run_marketing() -> dict:
    state = build_marketing_graph().invoke({})
    return {"status": "skeleton", "output": state.get("output", {})}


@app.post("/agents/delivery/run")
def run_delivery() -> dict:
    state = build_delivery_graph().invoke({})
    return {"status": "skeleton", "output": state.get("output", {})}


def main() -> None:
    uvicorn.run("agents.api:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
