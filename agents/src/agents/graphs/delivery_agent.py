from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from agents.config import settings
from agents.council_client import review_with_council
from agents.gateway_client import generate_structured_json
from agents.schemas import DeliveryAgentOutput, DeliveryDraftReport


class DeliveryAgentState(TypedDict, total=False):
    readiness_data: dict[str, Any]
    interview_notes: list[str]
    draft_report: dict[str, Any]
    council_review: dict[str, Any]
    output: dict[str, Any]


def fetch_delivery_inputs(state: DeliveryAgentState) -> DeliveryAgentState:
    if state.get("readiness_data") and state.get("interview_notes"):
        return {
            "readiness_data": state.get("readiness_data", {}),
            "interview_notes": state.get("interview_notes", []),
        }
    return {
        "readiness_data": {
            "overall_score": 67,
            "top_gaps": ["No AI policy baseline", "Limited automation governance", "Fragmented data ownership"],
            "strong_areas": ["Leadership buy-in", "Cloud infrastructure readiness"],
        },
        "interview_notes": [
            "Team spends significant time on repetitive admin tasks.",
            "Security and compliance require clearer model usage guardrails.",
            "Pilot should start in one revenue-adjacent workflow.",
        ],
    }


def build_draft_report(state: DeliveryAgentState) -> DeliveryAgentState:
    prompt = (
        "Create a draft AI readiness delivery report for sensitive internal documents.\n"
        "Return JSON with keys: summary, policy_suggestions (array), next_steps (array).\n"
        f"Readiness data: {json.dumps(state.get('readiness_data', {}), ensure_ascii=True)}\n"
        f"Interview notes: {json.dumps(state.get('interview_notes', []), ensure_ascii=True)}"
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
        payload = {"draft_report": improved, "council": council}
    else:
        payload = {"draft_report": draft, "council": council}
    try:
        validated = DeliveryAgentOutput.model_validate(payload)
    except ValidationError:
        validated = DeliveryAgentOutput(
            draft_report=DeliveryDraftReport(
                summary="Fallback delivery draft used due to parser mismatch.",
                policy_suggestions=["Define approved AI usage policy", "Create data handling and retention rules"],
                next_steps=["Run a scoped pilot", "Measure ROI and compliance outcomes"],
            ),
            council=council or {"enabled": False},
        )
    return {"output": validated.model_dump()}


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


def run_delivery_agent() -> DeliveryAgentOutput:
    app = build_delivery_graph()
    state = app.invoke({})
    return DeliveryAgentOutput.model_validate(state["output"])
