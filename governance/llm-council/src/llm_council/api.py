from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

from .schemas import CouncilRequest
from .service import as_openai_style_response, council_decide

app = FastAPI(title="AI Ready LLM Council", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/council/decide")
def decide(payload: dict[str, Any]) -> dict[str, Any]:
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
