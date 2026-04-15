from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from agents.gateway_client import generate_structured_json
from agents.schemas import CrmAgentOutput


class CrmAgentState(TypedDict, total=False):
    leads: list[dict[str, Any]]
    enriched: list[dict[str, Any]]
    llm_raw: dict[str, Any]
    output: dict[str, Any]


def fetch_leads(state: CrmAgentState) -> CrmAgentState:
    leads = state.get("leads")
    if leads:
        return {"leads": leads}
    return {
        "leads": [
            {
                "company_name": "Nordic Freight Systems",
                "website": "https://nordicfreight.example",
                "source": "manual-import",
                "industry_hint": "logistics software",
                "headcount_hint": "50-200",
                "signals": ["hiring devops", "new integration page"],
            },
            {
                "company_name": "Skylark LegalOps",
                "website": "https://skylarklegalops.example",
                "source": "csv-import",
                "industry_hint": "legal operations",
                "headcount_hint": "10-50",
                "signals": ["budget freeze notice", "no active hiring"],
            },
        ]
    }


def enrich_and_score(state: CrmAgentState) -> CrmAgentState:
    prompt = (
        "You are a B2B lead enrichment and ICP scoring assistant.\n"
        "Return JSON object with keys: leads, qualified_count, disqualified_count.\n"
        "Each lead must include: company_name, website, source, icp_score (0-100), "
        "qualification (qualified|nurture|disqualify), enrichment_summary, buying_signals (array), "
        "personalized_opener, disqualify_reason.\n"
        f"Input leads: {json.dumps(state.get('leads', []), ensure_ascii=True)}"
    )
    try:
        raw = generate_structured_json(prompt)
    except Exception:
        fallback_leads: list[dict[str, Any]] = []
        for lead in state.get("leads", []):
            signals = lead.get("signals", [])
            score = 72 if "hiring devops" in signals else 41
            qualification = "qualified" if score >= 70 else "nurture"
            fallback_leads.append(
                {
                    "company_name": lead.get("company_name", "Unknown"),
                    "website": lead.get("website", ""),
                    "source": lead.get("source", "unknown"),
                    "icp_score": score,
                    "qualification": qualification,
                    "enrichment_summary": "Fallback enrichment generated from available lead hints.",
                    "buying_signals": signals[:3],
                    "personalized_opener": f"Noticed your team at {lead.get('company_name', 'your company')} is scaling operations.",
                    "disqualify_reason": "" if qualification != "disqualify" else "Low ICP fit",
                }
            )
        raw = {
            "leads": fallback_leads,
            "qualified_count": sum(1 for item in fallback_leads if item["qualification"] == "qualified"),
            "disqualified_count": sum(1 for item in fallback_leads if item["qualification"] == "disqualify"),
        }
    return {"llm_raw": raw}


def format_output(state: CrmAgentState) -> CrmAgentState:
    try:
        validated = CrmAgentOutput.model_validate(state.get("llm_raw", {}))
    except ValidationError:
        leads = state.get("leads", [])
        normalized = [
            {
                "company_name": lead.get("company_name", "Unknown"),
                "website": lead.get("website", ""),
                "source": lead.get("source", "unknown"),
                "icp_score": 50,
                "qualification": "nurture",
                "enrichment_summary": "Fallback used due to parser mismatch.",
                "buying_signals": lead.get("signals", [])[:3],
                "personalized_opener": "Saw your recent updates and wanted to share an idea relevant to your team.",
                "disqualify_reason": "",
            }
            for lead in leads
        ]
        validated = CrmAgentOutput(
            leads=normalized,
            qualified_count=0,
            disqualified_count=0,
        )
    return {"output": validated.model_dump()}


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


def run_crm_agent() -> CrmAgentOutput:
    app = build_crm_graph()
    state = app.invoke({})
    return CrmAgentOutput.model_validate(state["output"])
