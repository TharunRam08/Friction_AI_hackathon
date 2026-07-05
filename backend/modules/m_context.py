# backend/modules/m_context.py
"""
Module 3 — Context Builder
Gathers real-time CRM business snapshot BEFORE reasoning starts.
Answers: "What is happening inside the company right now?"
"""
from data.crm_db import (
    get_financial_summary, get_deal_pipeline,
    get_customer_health, get_team_stats, get_decision_history
)

def build_context(intent: dict) -> dict:
    """
    Pulls live CRM data slices relevant to the question intent.
    Returns a structured business snapshot dict.
    """
    fin = get_financial_summary()
    pipeline = get_deal_pipeline()
    health = get_customer_health()
    team = get_team_stats()
    decisions = get_decision_history(5)  # last 5 decisions

    # Key Metrics Snapshot
    revenue = fin.get("latest_revenue", 0)
    profit = fin.get("latest_profit", 0)
    profit_margin = fin.get("avg_profit_margin_pct", 0)
    revenue_trend = fin.get("revenue_trend", "stable")
    headcount = team.get("total_headcount", 0)
    payroll = team.get("total_annual_payroll", 0)
    open_pipeline = pipeline.get("open_pipeline_value", 0)
    open_deals = pipeline.get("open_deal_count", 0)
    closed_won = pipeline.get("closed_won_value", 0)
    avg_ltv = health.get("avg_ltv", 0)
    at_risk_count = len(health.get("at_risk_accounts", []))
    at_risk_names = [a["name"] for a in health.get("at_risk_accounts", [])]

    # Department headcounts
    dept_map = {d["department"]: d for d in team.get("by_department", [])}
    sales_count = dept_map.get("Sales", {}).get("headcount", 0)
    ops_count = dept_map.get("Operations", {}).get("headcount", 0)
    tech_count = dept_map.get("Technology", {}).get("headcount", 0)

    # Recent decisions summary
    recent = [f"{d['date']}: {d['decision']} → {d['outcome']}" for d in decisions[:3]]

    snapshot = {
        "financials": {
            "monthly_revenue": revenue,
            "monthly_profit": profit,
            "profit_margin_pct": profit_margin,
            "revenue_trend": revenue_trend,
            "6m_total_profit": fin.get("total_profit_6m", 0),
        },
        "sales_pipeline": {
            "open_value": open_pipeline,
            "open_deals": open_deals,
            "closed_won_ytd": closed_won,
            "top_deals": pipeline.get("top_open_deals", [])[:3],
        },
        "customers": {
            "avg_ltv": avg_ltv,
            "high_churn_count": at_risk_count,
            "at_risk_accounts": at_risk_names,
        },
        "team": {
            "total_headcount": headcount,
            "annual_payroll": payroll,
            "sales_team_size": sales_count,
            "ops_team_size": ops_count,
            "tech_team_size": tech_count,
            "low_performers": len(team.get("low_performers", [])),
        },
        "recent_decisions": recent,
        # Narrative snapshot string for LLM context
        "snapshot_text": (
            f"Current business state: Revenue is ${revenue:,.0f}/month ({revenue_trend}), "
            f"profit margin {profit_margin}%. "
            f"Open sales pipeline: ${open_pipeline:,.0f} across {open_deals} deals. "
            f"Team: {headcount} employees (Sales:{sales_count}, Ops:{ops_count}, Tech:{tech_count}), "
            f"annual payroll ${payroll:,.0f}. "
            f"Customer base: avg LTV ${avg_ltv:,.0f}, {at_risk_count} high-churn accounts. "
            f"Last 3 decisions: {'; '.join(recent)}."
        )
    }
    return snapshot
