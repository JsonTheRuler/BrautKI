from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.config import settings
from agents.council_client import review_with_council
from agents.gateway_client import generate_structured_json


class DeliveryAgentState(TypedDict, total=False):
    readiness_data: dict[str, Any]
    interview_notes: list[str]
    draft_report: dict[str, Any]
    council_review: dict[str, Any]
    output: dict[str, Any]


def fetch_delivery_inputs(state: DeliveryAgentState) -> DeliveryAgentState:
    # TODO: pull AI readiness results and interview notes from data layer.
    return {
        "readiness_data": state.get("readiness_data", {}),
        "interview_notes": state.get("interview_notes", []),
    }


def build_draft_report(state: DeliveryAgentState) -> DeliveryAgentState:
    prompt = (
        "Create a draft AI readiness delivery report for sensitive internal documents.\n"
        "Return JSON with keys: summary, policy_suggestions (array), next_steps (array).\n"
        f"Readiness data: {state.get('readiness_data', {})}\n"
        f"Interview notes: {state.get('interview_notes', [])}"
    )
    try:
        draft = generate_structured_json(prompt, model_alias=settings.internal_secure_alias)
    except Exception:
        draft = {
            "summary": "Initial delivery draft (fallback)",
            "policy_suggestions": ["Create AI use-policy baseline", "Define data-handling guardrails"],
            "next_steps": ["Run pilot in one team", "Measure workflow time savings"],
        }
    return {"draft_report": draft}


def optional_council_review(state: DeliveryAgentState) -> DeliveryAgentState:
    if not settings.enable_council_review:
        return {"council_review": {"enabled": False}}
    try:
        reviewed = review_with_council(state.get("draft_report", {}))
        return {"council_review": {"enabled": True, "result": reviewed}}
    except Exception as exc:
        return {"council_review": {"enabled": True, "error": str(exc)}}


def format_output(state: DeliveryAgentState) -> DeliveryAgentState:
    draft = state.get("draft_report", {})
    council = state.get("council_review", {})
    if council.get("enabled") and "result" in council:
        improved = council["result"].get("improved_report", draft)
        return {"output": {"draft_report": improved, "council": council}}
    return {"output": {"draft_report": draft, "council": council}}


def build_delivery_graph():
    graph = StateGraph(DeliveryAgentState)
    graph.add_node("fetch_delivery_inputs", fetch_delivery_inputs)
    graph.add_node("build_draft_report", build_draft_report)
    graph.add_node("optional_council_review", optional_council_review)
    graph.add_node("format_output", format_output)
    graph.set_entry_point("fetch_delivery_inputs")
    graph.add_edge("fetch_delivery_inputs", "build_draft_report")
    graph.add_edge("build_draft_report", "optional_council_review")
    graph.add_edge("optional_council_review", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()
