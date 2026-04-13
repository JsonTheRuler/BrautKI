from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from .config import settings
from .schemas import CouncilRequest, CouncilResponse, CouncilVote


def _chat_completion_payload(alias: str, prompt: str) -> dict[str, Any]:
    return {
        "model": alias,
        "messages": [
            {"role": "system", "content": "You are a council member. Be concise and actionable."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }


def _invoke_gateway(alias: str, prompt: str) -> CouncilVote:
    payload = _chat_completion_payload(alias=alias, prompt=prompt)
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{settings.gateway_url.rstrip('/')}/v1/chat/completions", json=payload)
        response.raise_for_status()
        body = response.json()
    answer = body["choices"][0]["message"]["content"]
    return CouncilVote(alias=alias, answer=answer, confidence=0.5)


def _build_member_prompt(req: CouncilRequest) -> str:
    context = req.context if isinstance(req.context, str) else json.dumps(req.context, ensure_ascii=True)
    return (
        "Question:\n"
        f"{req.question}\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Return:\n"
        "1) concise answer\n"
        "2) key risks\n"
        "3) confidence from 0.0 to 1.0"
    )


def _synthesize(req: CouncilRequest, votes: list[CouncilVote]) -> tuple[str, str]:
    votes_blob = json.dumps([vote.model_dump() for vote in votes], ensure_ascii=True)
    prompt = (
        "You are chair of an LLM council.\n"
        "Given the question, context, and member votes, produce JSON with keys:\n"
        "final_answer (string), rationale (string).\n\n"
        f"Question: {req.question}\n"
        f"Context: {json.dumps(req.context, ensure_ascii=True) if not isinstance(req.context, str) else req.context}\n"
        f"Votes: {votes_blob}"
    )
    payload = _chat_completion_payload(settings.synthesis_alias, prompt)

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{settings.gateway_url.rstrip('/')}/v1/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed["final_answer"], parsed["rationale"]
    except Exception:
        fallback_answer = votes[0].answer if votes else "No member answer available."
        fallback_rationale = "Fallback synthesis used due to synthesis parsing failure."
        return fallback_answer, fallback_rationale


def council_decide(req: CouncilRequest) -> CouncilResponse:
    prompt = _build_member_prompt(req)
    votes: list[CouncilVote] = []

    for alias in settings.member_aliases:
        try:
            votes.append(_invoke_gateway(alias, prompt))
        except Exception:
            votes.append(CouncilVote(alias=alias, answer="Member unavailable.", confidence=0.0))

    final_answer, rationale = _synthesize(req, votes)
    return CouncilResponse(final_answer=final_answer, rationale=rationale, votes=votes)


def as_openai_style_response(result: CouncilResponse, requested_model: str = "council-meta") -> dict[str, Any]:
    message = {
        "final_answer": result.final_answer,
        "rationale": result.rationale,
        "votes": [vote.model_dump() for vote in result.votes],
    }
    return {
        "id": f"council-{uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now(tz=timezone.utc).timestamp()),
        "model": requested_model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(message, ensure_ascii=True)},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "council_result": message,
    }
