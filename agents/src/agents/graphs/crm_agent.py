from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class CrmAgentState(TypedDict, total=False):
    leads: list[dict[str, Any]]
    enriched: list[dict[str, Any]]
    output: dict[str, Any]


def fetch_leads(state: CrmAgentState) -> CrmAgentState:
    # TODO: Load new leads from data layer.
    return {"leads": state.get("leads", [])}


def enrich_and_score(state: CrmAgentState) -> CrmAgentState:
    # TODO: Call gateway for enrichment + A/B/C scoring + outreach suggestion.
    return {"enriched": state.get("leads", [])}


def format_output(state: CrmAgentState) -> CrmAgentState:
    return {"output": {"leads": state.get("enriched", [])}}


def build_crm_graph():
    graph = StateGraph(CrmAgentState)
    graph.add_node("fetch_leads", fetch_leads)
    graph.add_node("enrich_and_score", enrich_and_score)
    graph.add_node("format_output", format_output)
    graph.set_entry_point("fetch_leads")
    graph.add_edge("fetch_leads", "enrich_and_score")
    graph.add_edge("enrich_and_score", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()
