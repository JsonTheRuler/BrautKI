from __future__ import annotations

from agents.graphs.crm_agent import run_crm_agent
from agents.graphs.delivery_agent import run_delivery_agent
from agents.graphs.marketing_agent import run_marketing_agent


def main() -> None:
    crm = run_crm_agent()
    assert crm.leads, "CRM output should include at least one lead"
    actual_q = sum(1 for lead in crm.leads if lead.qualification == "qualified")
    actual_d = sum(1 for lead in crm.leads if lead.qualification == "disqualify")
    assert crm.qualified_count == actual_q, "qualified_count should match actual qualified leads"
    assert crm.disqualified_count == actual_d, "disqualified_count should match actual disqualified leads"

    marketing = run_marketing_agent()
    assert marketing.drafts, "Marketing output should include at least one draft"
    assert marketing.draft_count == len(marketing.drafts)

    delivery = run_delivery_agent()
    assert delivery.draft_report.summary, "Delivery report should include summary"
    assert delivery.draft_report.next_steps, "Delivery report should include next steps"

    print("Core agents test passed: CRM, Marketing, Delivery outputs validated.")


if __name__ == "__main__":
    main()
