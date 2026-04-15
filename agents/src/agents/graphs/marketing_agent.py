from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from agents.gateway_client import generate_structured_json
from agents.schemas import MarketingAgentOutput


class MarketingAgentState(TypedDict, total=False):
    content_assets: list[dict[str, Any]]
    drafts: list[dict[str, Any]]
    llm_raw: dict[str, Any]
    output: dict[str, Any]


def fetch_content_assets(state: MarketingAgentState) -> MarketingAgentState:
    assets = state.get("content_assets")
    if assets:
        return {"content_assets": assets}
    return {
        "content_assets": [
            {
                "title": "AI Readiness Workshop",
                "asset_type": "service-page",
                "summary": "Two-day leadership workshop mapping AI opportunities and risks.",
            },
            {
                "title": "Inbox Automation Case Study",
                "asset_type": "case-study",
                "summary": "Reduced manual triage by 70% using AI agent orchestration.",
            },
        ]
    }


def generate_marketing_drafts(state: MarketingAgentState) -> MarketingAgentState:
    prompt = (
        "You are a B2B content strategist.\n"
        "Return JSON object with keys: drafts (array) and draft_count.\n"
        "Each draft must include: asset_title, channel, hook, draft_text, cta.\n"
        "Generate channel-specific outputs for linkedin, blog, and newsletter when possible.\n"
        f"Assets: {json.dumps(state.get('content_assets', []), ensure_ascii=True)}"
    )
    try:
        raw = generate_structured_json(prompt)
    except Exception:
        drafts: list[dict[str, Any]] = []
        for asset in state.get("content_assets", []):
            title = asset.get("title", "Untitled")
            drafts.append(
                {
                    "asset_title": title,
                    "channel": "linkedin",
                    "hook": f"What changes when {title.lower()} is executed well?",
                    "draft_text": f"{title}: practical lessons from real delivery teams and measurable operations impact.",
                    "cta": "Reply if you want the implementation checklist.",
                }
            )
        raw = {"drafts": drafts, "draft_count": len(drafts)}
    return {"llm_raw": raw}


def format_output(state: MarketingAgentState) -> MarketingAgentState:
    try:
        validated = MarketingAgentOutput.model_validate(state.get("llm_raw", {}))
    except ValidationError:
        drafts = []
        for asset in state.get("content_assets", []):
            title = asset.get("title", "Untitled")
            drafts.append(
                {
                    "asset_title": title,
                    "channel": "linkedin",
                    "hook": "Fallback draft generated.",
                    "draft_text": f"{title} can be adapted into a full campaign bundle.",
                    "cta": "Book a planning call.",
                }
            )
        validated = MarketingAgentOutput(drafts=drafts, draft_count=len(drafts))
    return {"output": validated.model_dump()}


def build_marketing_graph():
    graph = StateGraph(MarketingAgentState)
    graph.add_node("fetch_content_assets", fetch_content_assets)
    graph.add_node("generate_marketing_drafts", generate_marketing_drafts)
    graph.add_node("format_output", format_output)
    graph.set_entry_point("fetch_content_assets")
    graph.add_edge("fetch_content_assets", "generate_marketing_drafts")
    graph.add_edge("generate_marketing_drafts", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


def run_marketing_agent() -> MarketingAgentOutput:
    app = build_marketing_graph()
    state = app.invoke({})
    return MarketingAgentOutput.model_validate(state["output"])
