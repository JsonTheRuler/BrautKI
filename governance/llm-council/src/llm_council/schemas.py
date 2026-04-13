from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CouncilRequest(BaseModel):
    question: str
    context: dict[str, Any] | str = Field(default_factory=dict)


class CouncilVote(BaseModel):
    alias: str
    answer: str
    confidence: float


class CouncilResponse(BaseModel):
    final_answer: str
    rationale: str
    votes: list[CouncilVote]
