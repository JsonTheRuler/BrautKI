from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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
    email_limit: int = Field(default=10, ge=1, le=100)


class InboxAgentResponse(BaseModel):
    result: InboxAgentOutput


class CrmLeadItem(BaseModel):
    company_name: str
    website: str
    source: str
    icp_score: int = Field(ge=0, le=100)
    qualification: str = Field(description="qualified | nurture | disqualify")
    enrichment_summary: str
    buying_signals: list[str]
    personalized_opener: str
    disqualify_reason: str = ""


class CrmAgentOutput(BaseModel):
    leads: list[CrmLeadItem]
    qualified_count: int
    disqualified_count: int

    @model_validator(mode="after")
    def sync_counts(self) -> "CrmAgentOutput":
        self.qualified_count = sum(1 for lead in self.leads if lead.qualification == "qualified")
        self.disqualified_count = sum(1 for lead in self.leads if lead.qualification == "disqualify")
        return self


class CrmAgentResponse(BaseModel):
    status: str
    output: CrmAgentOutput


class MarketingDraftItem(BaseModel):
    asset_title: str
    channel: str = Field(description="linkedin | blog | newsletter | x")
    hook: str
    draft_text: str
    cta: str


class MarketingAgentOutput(BaseModel):
    drafts: list[MarketingDraftItem]
    draft_count: int

    @model_validator(mode="after")
    def sync_draft_count(self) -> "MarketingAgentOutput":
        self.draft_count = len(self.drafts)
        return self


class MarketingAgentResponse(BaseModel):
    status: str
    output: MarketingAgentOutput


class DeliveryDraftReport(BaseModel):
    summary: str
    policy_suggestions: list[str]
    next_steps: list[str]


class DeliveryAgentOutput(BaseModel):
    draft_report: DeliveryDraftReport
    council: dict


class DeliveryAgentResponse(BaseModel):
    status: str
    output: DeliveryAgentOutput
