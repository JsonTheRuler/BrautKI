from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class MarketingAgentState(TypedDict, total=False):
    content_assets: list[dict[str, Any]]
    drafts: list[dict[str, Any]]
    output: dict[str, Any]


def fetch_content_assets(state: MarketingAgentState) -> MarketingAgentState:
    # TODO: Pull website copy/blog/case study documents from data layer.
    return {"content_assets": state.get("content_assets", [])}


def generate_marketing_drafts(state: MarketingAgentState) -> MarketingAgentState:
    # TODO: Call gateway to create blog drafts + LinkedIn updates + LP variant ideas.
    return {"drafts": []}


def format_output(state: MarketingAgentState) -> MarketingAgentState:
    return {"output": {"drafts": state.get("drafts", [])}}


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
