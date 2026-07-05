# backend/main.py
"""
Friction — Full 16-Module Cognitive Pipeline
Routes queries through LOW / MEDIUM / HIGH friction paths.
"""
import os
import sqlite3
import json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from groq import Groq
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from modules.m01_intent import get_intent
from modules.m02_friction import get_friction_level
from modules.m03_context import build_context
from modules.m04_memory import get_past_context
from modules.m05_rootcause import find_root_cause
from modules.m06_debate import run_debate
from modules.m08_validate import validate_evidence_and_constraints, self_review
from modules.m07_scenarios import run_scenarios_and_regret
from modules.m09_nemotron import run_nemotron_synthesis

# CRM Data helpers
from data.crm_db import (
    get_financial_summary, get_deal_pipeline,
    get_customer_health, get_team_stats, get_decision_history,
    get_product_metrics, get_inventory_status, get_campaign_performance,
    get_support_metrics, get_supplier_health, get_expense_breakdown,
    get_kpi_summary, get_contracts_summary
)

# ── Config ───────────────────────────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

CRM_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "crm.db")

app = FastAPI(title="Friction API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


# ── Greeting Detector ─────────────────────────────────────────────────────────
def is_general_greeting(text: str) -> bool:
    cleaned = text.lower().strip().rstrip("?.!")
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon",
        "good evening", "who are you", "what is this", "what can you do", "help",
        "start", "welcome", "test"
    }
    if cleaned in greetings:
        return True
    if len(cleaned.split()) <= 2 and not any(
        w in cleaned for w in [
            "expand", "hire", "buy", "sell", "product", "launch", "branch",
            "price", "cost", "revenue", "profit", "salary", "warehouse",
            "customer", "deal", "team", "risk"
        ]
    ):
        return True
    return False


# ── Master Pipeline ───────────────────────────────────────────────────────────
@app.post("/reason")
async def reason(request: QueryRequest):
    question = request.question

    # ── GREETING FAST PATH ───────────────────────────────────────────────────
    if is_general_greeting(question):
        fin = get_financial_summary()
        pipeline = get_deal_pipeline()
        team = get_team_stats()
        health = get_customer_health()
        return {
            "question": question,
            "friction_level": "LOW",
            "pipeline_executed": ["Intent", "Context"],
            "intent": {"goal": "initialize reasoning", "constraints": ["awaiting business scenario"]},
            "context": {"snapshot_text": "Systems ready."},
            "past_memory": (
                f"Friction CRM connected: {team.get('total_headcount',0)} employees, "
                f"${pipeline.get('open_pipeline_value',0):,.0f} open pipeline, "
                f"${fin.get('latest_revenue',0):,.0f} monthly revenue, "
                f"{health.get('avg_ltv',0):,.0f} avg customer LTV."
            ),
            "past_memory_score": 1.0,
            "department_views": [
                {"stance": "Support", "reasons": ["Finance module online. Revenue trending up."]},
                {"stance": "Support", "reasons": ["Operations module online. Pipeline healthy."]},
                {"stance": "Support", "reasons": ["Sales module online. 31 active deals tracked."]},
                {"stance": "Support", "reasons": ["HR module online. Team data loaded."]}
            ],
            "output": {
                "verdict": "Welcome to Friction AI",
                "narrative": (
                    f"Friction is live and connected to your CRM knowledge base. "
                    f"Your business currently has ${fin.get('latest_revenue',0):,.0f} in monthly revenue "
                    f"({fin.get('revenue_trend','stable')} trend), {team.get('total_headcount',0)} employees, "
                    f"and ${pipeline.get('open_pipeline_value',0):,.0f} in open pipeline value. "
                    f"All 5 data sources are connected and ready. Ask a strategic business question to activate the full cognitive pipeline."
                ),
                "key_stats": [
                    {"label": "Monthly Revenue", "value": f"${fin.get('latest_revenue',0):,.0f}", "trend": fin.get("revenue_trend","stable")},
                    {"label": "Open Pipeline", "value": f"${pipeline.get('open_pipeline_value',0):,.0f}", "trend": "stable"},
                    {"label": "Team Size", "value": str(team.get("total_headcount",0)) + " employees", "trend": "stable"},
                    {"label": "Avg Customer LTV", "value": f"${health.get('avg_ltv',0):,.0f}", "trend": "stable"},
                ],
                "confidence": 100,
                "confidence_breakdown": {"agreement": 100, "memory_match": 100, "evidence": 100, "scenario_stability": 100},
                "departments": [
                    {"name": "Finance", "status": "yes", "score": 100, "reason": "Module online"},
                    {"name": "Operations", "status": "yes", "score": 100, "reason": "Module online"},
                    {"name": "Sales", "status": "yes", "score": 100, "reason": "Module online"},
                    {"name": "HR", "status": "yes", "score": 100, "reason": "Module online"},
                ],
                "action_plan": [
                    {"step": "Ask a strategic business question to begin", "timeframe": "now"},
                    {"step": "Click a data source in the sidebar to explore your CRM data", "timeframe": "anytime"},
                ],
                "evidence_score": 100,
                "scenarios": [],
                "devils_advocate": [],
                "regret_choice": "",
                "constraints_check": [],
                "self_review": "All systems nominal.",
                "if_ignored": [],
            },
            "confidence": {"confidence": 100.0, "agreement_score": 1.0, "memory_match": 1.0, "evidence_score": 1.0, "scenario_stability": 1.0}
        }

    # ── PHASE 1: UNDERSTAND ──────────────────────────────────────────────────
    # Run Intent + Context in parallel
    intent = None
    context = None
    with ThreadPoolExecutor(max_workers=2) as ex:
        future_intent = ex.submit(get_intent, question, client)
        intent = future_intent.result()

    goal = intent.get("goal", "")

    # Friction Engine — decides pipeline depth
    friction = get_friction_level(question, intent, client)
    friction_level = friction.get("level", "MEDIUM")

    # Context Builder — always run (reads CRM, no LLM call)
    context = build_context(intent)

    # Business Memory Retrieval
    past_memory, memory_score = get_past_context(question, goal, intent)
    non_neg_score = max(0.0, memory_score)

    pipeline_executed = ["Intent", "Friction", "Context", "Memory"]

    # ── PHASE 2: ANALYZE (MEDIUM + HIGH only) ────────────────────────────────
    root_cause = {}
    views = []
    validation = {}

    if friction_level in ("MEDIUM", "HIGH"):
        context_text = context.get("snapshot_text", "")

        with ThreadPoolExecutor(max_workers=2) as ex:
            future_rootcause = ex.submit(find_root_cause, question, context_text, client)
            future_debate = ex.submit(run_debate, question, goal, past_memory, client)
            root_cause = future_rootcause.result()
            views = future_debate.result()

        pipeline_executed += ["Root Cause", "Debate", "Evidence"]
        validation = validate_evidence_and_constraints(question, views, context, client)

    # ── PHASE 3: REASON (HIGH only) ──────────────────────────────────────────
    scenarios_data = {}

    if friction_level == "HIGH":
        debate_summary = "; ".join([
            f"{['Finance','Operations','Sales','HR'][i]}: {v.get('stance','')} — {v.get('reasons',[''])[0]}"
            for i, v in enumerate(views) if v
        ])
        scenarios_data = run_scenarios_and_regret(
            question, intent, context.get("snapshot_text", ""),
            debate_summary, client
        )
        pipeline_executed += ["Scenarios", "Devil's Advocate", "Regret"]

    # ── PHASE 4: VERIFY (MEDIUM + HIGH) ──────────────────────────────────────
    self_review_text = ""
    if friction_level in ("MEDIUM", "HIGH"):
        all_outputs_summary = {
            "intent": intent, "friction": friction,
            "memory_score": non_neg_score,
            "validation": validation
        }
        self_review_text = self_review(question, all_outputs_summary, client)
        pipeline_executed += ["Confidence", "Constraints", "Self Review"]

    # ── PHASE 5: DECIDE — Final Synthesis ────────────────────────────────────
    pipeline_executed += ["Synthesis", "Explainability", "Learning"]

    output = run_nemotron_synthesis(
        question=question,
        intent=intent,
        friction=friction,
        context=context,
        past_memory=past_memory,
        past_memory_score=non_neg_score,
        root_cause=root_cause,
        views=views if views else [],
        validation=validation,
        scenarios_data=scenarios_data,
        self_review_text=self_review_text,
        client_groq=client
    )

    # ── Format response for frontend ─────────────────────────────────────────
    status_map = {"yes": "Support", "no": "Against", "wait": "Neutral"}
    depts = output.get("departments", [])
    formatted_views = []
    if len(depts) == 4:
        for dept in depts:
            formatted_views.append({
                "stance": status_map.get(dept.get("status"), "Neutral"),
                "reasons": [f"{dept.get('reason', '')} ({dept.get('score', 75)}%)"]
            })
    else:
        formatted_views = views

    # ── Calculate Mathematical Confidence Score Dynamically ──────────────────
    # 1. Agreement (4 agree = 100, 3 agree = 75, 2-2 split = 50, 3 against = 25)
    agreement = 50
    if views:
        stances = [v.get("stance", "neutral").lower() for v in views if v]
        yes_count = sum(1 for s in stances if s in ("yes", "support", "for"))
        no_count = sum(1 for s in stances if s in ("no", "against"))
        total_active = len(stances)
        if total_active > 0:
            if yes_count == total_active or no_count == total_active:
                agreement = 100
            elif yes_count >= 3 or no_count >= 3:
                agreement = 75
            elif yes_count == 2 and no_count == 2:
                agreement = 50
            else:
                agreement = 25

    # 2. Memory match
    memory_match = min(100, max(0, int(non_neg_score * 100)))

    # 3. Evidence (Module 13 validate phase evidence score)
    evidence = validation.get("evidence_score", 70) if validation else 70

    # 4. Scenario stability
    scenario_stability = 60
    if scenarios_data:
        scenarios_list = scenarios_data.get("scenarios", [])
        if scenarios_list:
            risks = [s.get("risk", "Medium").lower() for s in scenarios_list if s]
            if all(r == "low" for r in risks):
                scenario_stability = 80
            elif all(r == "high" for r in risks):
                scenario_stability = 40
            else:
                scenario_stability = 60

    calculated_confidence = int(round(0.35 * agreement + 0.25 * memory_match + 0.20 * evidence + 0.20 * scenario_stability))

    # Overwrite LLM payload values with programmatic ground-truth math
    output["confidence"] = calculated_confidence
    output["confidence_breakdown"] = {
        "agreement": agreement,
        "memory_match": memory_match,
        "evidence": evidence,
        "scenario_stability": scenario_stability
    }

    confidence_data = {
        "confidence": calculated_confidence,
        "agreement_score": agreement / 100.0,
        "memory_match": memory_match / 100.0,
        "evidence_score": evidence / 100.0,
        "scenario_stability": scenario_stability / 100.0,
    }

    # Build recommendation text (backward compat with old UI fields)
    rec_parts = [f"**Verdict**: {output.get('verdict', '')}"]
    if output.get("mistake_context"):
        rec_parts.append(f"**Past Case**: {output['mistake_context']}")
    if output.get("pattern_match"):
        rec_parts.append(f"**Pattern Match**: {output['pattern_match']}")
    if output.get("action_plan"):
        plan = ", ".join([f"{a['step']} ({a['timeframe']})" for a in output["action_plan"]])
        rec_parts.append(f"**Action Plan**: {plan}")
    if output.get("if_ignored"):
        rec_parts.append(f"**Risk If Ignored**: {' | '.join(output['if_ignored'])}")

    return {
        "question": question,
        "friction_level": friction_level,
        "pipeline_executed": pipeline_executed,
        "intent": intent,
        "context": context,
        "past_memory": past_memory,
        "past_memory_score": non_neg_score,
        "department_views": formatted_views,
        "recommendation": "\n\n".join(rec_parts),
        "output": output,  # Full rich output object
        "confidence": confidence_data,
    }


# ── Data Sources API ──────────────────────────────────────────────────────────
@app.get("/data-sources")
async def data_sources_summary():
    # Load summaries
    fin = get_financial_summary()
    pipeline = get_deal_pipeline()
    health = get_customer_health()
    team = get_team_stats()
    decisions = get_decision_history(25)
    products = get_product_metrics()
    inventory = get_inventory_status()
    campaigns = get_campaign_performance()
    support = get_support_metrics()
    suppliers = get_supplier_health()
    expenses = get_expense_breakdown()
    kpis = get_kpi_summary()
    contracts = get_contracts_summary()

    # Query counts from DB
    tables = [
        "customers", "deals", "financials", "team", "decisions",
        "products", "inventory", "campaigns", "support_tickets",
        "suppliers", "expenses", "kpis", "contracts"
    ]
    conn = sqlite3.connect(CRM_DB_PATH)
    cur = conn.cursor()
    counts = {}
    for tbl in tables:
        counts[tbl] = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    conn.close()

    return {
        "sources": [
            {
                "id": "customers",
                "label": "Customers",
                "icon": "users",
                "row_count": counts["customers"],
                "status": "connected",
                "summary": f"Avg LTV ${health['avg_ltv']:,.0f} • {len(health.get('at_risk_accounts', []))} high-risk accounts",
                "tags": ["CRM", "Retention"]
            },
            {
                "id": "deals",
                "label": "Deals Pipeline",
                "icon": "trending-up",
                "row_count": counts["deals"],
                "status": "connected",
                "summary": f"Open pipeline ${pipeline['open_pipeline_value']:,.0f} • {pipeline['open_deal_count']} active deals",
                "tags": ["Sales", "Pipeline"]
            },
            {
                "id": "financials",
                "label": "Financials",
                "icon": "bar-chart",
                "row_count": counts["financials"],
                "status": "connected",
                "summary": f"Latest revenue ${fin['latest_revenue']:,.0f} • {fin['avg_profit_margin_pct']}% avg margin",
                "tags": ["Finance", "P&L"]
            },
            {
                "id": "team",
                "label": "Team",
                "icon": "people",
                "row_count": counts["team"],
                "status": "connected",
                "summary": f"{team['total_headcount']} employees • ${team['total_annual_payroll']:,.0f} annual payroll",
                "tags": ["HR", "Talent"]
            },
            {
                "id": "decisions",
                "label": "Past Decisions",
                "icon": "clock",
                "row_count": counts["decisions"],
                "status": "connected",
                "summary": f"{sum(1 for d in decisions if d['outcome']=='Success')} successes • {sum(1 for d in decisions if d['outcome']=='Failed')} failures",
                "tags": ["Memory", "History"]
            },
            {
                "id": "products",
                "label": "Products & SKUs",
                "icon": "package",
                "row_count": counts["products"],
                "status": "connected",
                "summary": f"YTD Product Rev ${products['total_product_revenue_ytd']:,.0f} • Avg Margin {products['avg_portfolio_margin']}%",
                "tags": ["Inventory", "Margin"]
            },
            {
                "id": "inventory",
                "label": "Inventory",
                "icon": "archive",
                "row_count": counts["inventory"],
                "status": "connected",
                "summary": f"{inventory['needs_immediate_reorder']} critical items need reorder • Avg Supply {inventory['avg_days_of_supply']} days",
                "tags": ["Logistics", "Warehouse"]
            },
            {
                "id": "campaigns",
                "label": "Marketing Campaigns",
                "icon": "target",
                "row_count": counts["campaigns"],
                "status": "connected",
                "summary": f"Spent ${campaigns['total_spend']:,.0f} • Overall ROI {campaigns['overall_roi_pct']}%",
                "tags": ["Marketing", "ROI"]
            },
            {
                "id": "support_tickets",
                "label": "Support Tickets",
                "icon": "help-circle",
                "row_count": counts["support_tickets"],
                "status": "connected",
                "summary": f"Avg CSAT {support['avg_csat']}/5 • {len(support['critical_open'])} critical tickets open",
                "tags": ["Support", "CSAT"]
            },
            {
                "id": "suppliers",
                "label": "Suppliers & Vendors",
                "icon": "truck",
                "row_count": counts["suppliers"],
                "status": "connected",
                "summary": f"Avg Reliability {suppliers['avg_reliability_score']}/100 • {len(suppliers['high_risk_suppliers'])} high-risk suppliers",
                "tags": ["Vendor", "Operations"]
            },
            {
                "id": "expenses",
                "label": "Expenses",
                "icon": "credit-card",
                "row_count": counts["expenses"],
                "status": "connected",
                "summary": f"Latest Monthly Expense ${expenses['latest_total']:,.0f} • 6M Avg ${expenses['avg_monthly_expenses_6m']:,.0f}",
                "tags": ["Finance", "Expenses"]
            },
            {
                "id": "kpis",
                "label": "Quarterly KPIs",
                "icon": "activity",
                "row_count": counts["kpis"],
                "status": "connected",
                "summary": f"MRR ${kpis['latest_mrr']:,.0f} • Churn {kpis['latest_churn_pct']}% • NPS {kpis['latest_nps']}",
                "tags": ["KPIs", "SaaS"]
            },
            {
                "id": "contracts",
                "label": "Contracts & ARR",
                "icon": "file-text",
                "row_count": counts["contracts"],
                "status": "connected",
                "summary": f"Total ARR ${contracts['total_arr']:,.0f} • At-Risk ARR ${contracts['at_risk_arr']:,.0f}",
                "tags": ["Contracts", "ARR"]
            },
        ]
    }


@app.get("/data-sources/{table}")
async def data_source_rows(table: str, limit: int = 100):
    allowed = {
        "customers", "deals", "financials", "team", "decisions",
        "products", "inventory", "campaigns", "support_tickets",
        "suppliers", "expenses", "kpis", "contracts"
    }
    if table not in allowed:
        return {"error": "Invalid table", "rows": [], "columns": []}
    conn = sqlite3.connect(CRM_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(f"SELECT * FROM {table} LIMIT ?", (limit,)).fetchall()
    columns = [d[0] for d in cur.description] if rows else []
    conn.close()
    return {"table": table, "columns": columns, "rows": [dict(r) for r in rows], "total": len(rows)}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
