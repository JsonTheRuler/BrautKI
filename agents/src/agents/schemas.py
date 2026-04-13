from __future__ import annotations

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    title: str
    start_iso: str
    end_iso: str


class EmailRecord(BaseModel):
    id: str
    from_address: str
    to_address: str
    subject: str
    body: str


class EmailTriageItem(BaseModel):
    email_id: str
    classification: str = Field(description="important | can_wait | spam_like")
    rationale: str
    draft_reply: str
    suggested_task: str
    suggested_calendar_block: str


class InboxAgentOutput(BaseModel):
    triage: list[EmailTriageItem]


class InboxAgentRequest(BaseModel):
    email_limit: int = 10


class InboxAgentResponse(BaseModel):
    result: InboxAgentOutput
