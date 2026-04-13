from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from agents.gateway_client import generate_structured_json
from agents.schemas import InboxAgentOutput
from agents.tools.inbox_tools import get_calendar_events, get_recent_emails, save_draft_reply


class InboxAgentState(TypedDict, total=False):
    email_limit: int
    emails: list[dict[str, Any]]
    calendar_events: list[dict[str, Any]]
    llm_raw: dict[str, Any]
    output: dict[str, Any]


def fetch_context(state: InboxAgentState) -> InboxAgentState:
    emails = [item.model_dump() for item in get_recent_emails(limit=state.get("email_limit", 10))]
    events = [item.model_dump() for item in get_calendar_events()]
    return {"emails": emails, "calendar_events": events}


def llm_triage(state: InboxAgentState) -> InboxAgentState:
    prompt = (
        "You are an executive inbox assistant.\n"
        "Classify each email as important, can_wait, or spam_like.\n"
        "Return JSON object with key 'triage' as array. Each element must include:\n"
        "email_id, classification, rationale, draft_reply, suggested_task, suggested_calendar_block.\n\n"
        f"Emails:\n{json.dumps(state['emails'], ensure_ascii=True)}\n\n"
        f"Calendar events:\n{json.dumps(state['calendar_events'], ensure_ascii=True)}"
    )
    try:
        raw = generate_structured_json(prompt)
    except Exception:
        raw = {
            "triage": [
                {
                    "email_id": email["id"],
                    "classification": "can_wait",
                    "rationale": "Gateway unavailable; produced safe fallback triage.",
                    "draft_reply": "Thanks for reaching out. We received your email and will follow up shortly.",
                    "suggested_task": "Review this message and convert to CRM task if needed.",
                    "suggested_calendar_block": "30-minute triage block tomorrow morning.",
                }
                for email in state["emails"]
            ]
        }
    return {"llm_raw": raw}


def format_output(state: InboxAgentState) -> InboxAgentState:
    try:
        validated = InboxAgentOutput.model_validate(state["llm_raw"])
    except ValidationError:
        # Minimal fallback so API remains usable even if LLM format drifts.
        validated = InboxAgentOutput(
            triage=[
                {
                    "email_id": email["id"],
                    "classification": "can_wait",
                    "rationale": "Fallback used due to parser mismatch.",
                    "draft_reply": "Thanks for your email. We will review and get back shortly.",
                    "suggested_task": "Review and prioritize this email manually.",
                    "suggested_calendar_block": "30-minute inbox review block tomorrow morning.",
                }
                for email in state["emails"]
            ]
        )

    for item in validated.triage:
        save_draft_reply(item.email_id, item.draft_reply)

    return {"output": validated.model_dump()}


def build_inbox_graph():
    graph = StateGraph(InboxAgentState)
    graph.add_node("fetch_context", fetch_context)
    graph.add_node("llm_triage", llm_triage)
    graph.add_node("format_output", format_output)

    graph.set_entry_point("fetch_context")
    graph.add_edge("fetch_context", "llm_triage")
    graph.add_edge("llm_triage", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


def run_inbox_agent(email_limit: int = 10) -> InboxAgentOutput:
    app = build_inbox_graph()
    state = app.invoke({"email_limit": email_limit})
    return InboxAgentOutput.model_validate(state["output"])
