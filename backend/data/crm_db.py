# backend/data/crm_db.py
"""
CRM Database Query Helper — reads live context slices from crm.db (13 tables).
"""
import sqlite3
import os
from typing import Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "crm.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── TABLE 1: Financials ───────────────────────────────────────────────────────
def get_financial_summary() -> Dict[str, Any]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM financials ORDER BY month DESC LIMIT 6").fetchall()
    conn.close()
    if not rows:
        return {}
    latest, oldest = rows[0], rows[-1]
    trend = "growing" if latest["revenue"] > oldest["revenue"] else "declining"
    margin_avg = round(sum(r["profit"]/r["revenue"]*100 for r in rows)/len(rows), 1)
    return {
        "latest_month": latest["month"],
        "latest_revenue": latest["revenue"],
        "latest_profit": latest["profit"],
        "latest_headcount": latest["headcount"],
        "revenue_trend": trend,
        "avg_profit_margin_pct": margin_avg,
        "total_revenue_6m": sum(r["revenue"] for r in rows),
        "total_profit_6m": sum(r["profit"] for r in rows),
        "months": [dict(r) for r in rows],
    }


# ── TABLE 2: Deals ────────────────────────────────────────────────────────────
def get_deal_pipeline() -> Dict[str, Any]:
    conn = _conn()
    stages = conn.execute("""SELECT stage, COUNT(*) as count, SUM(value) as total_value,
        AVG(probability) as avg_prob FROM deals GROUP BY stage""").fetchall()
    top = conn.execute("""SELECT customer_name, title, value, stage, probability, owner
        FROM deals WHERE stage NOT IN ('Closed-Won','Closed-Lost') ORDER BY value DESC LIMIT 5""").fetchall()
    totals = conn.execute(
        "SELECT SUM(value) as pipeline, COUNT(*) as count FROM deals WHERE stage NOT IN ('Closed-Won','Closed-Lost')"
    ).fetchone()
    won = conn.execute("SELECT SUM(value) as won FROM deals WHERE stage='Closed-Won'").fetchone()
    conn.close()
    return {
        "open_pipeline_value": totals["pipeline"] or 0,
        "open_deal_count": totals["count"] or 0,
        "closed_won_value": won["won"] or 0,
        "by_stage": [dict(r) for r in stages],
        "top_open_deals": [dict(r) for r in top],
    }


# ── TABLE 3: Customers ────────────────────────────────────────────────────────
def get_customer_health() -> Dict[str, Any]:
    conn = _conn()
    churn = conn.execute(
        "SELECT churn_risk, COUNT(*) as count, AVG(ltv) as avg_ltv FROM customers GROUP BY churn_risk"
    ).fetchall()
    at_risk = conn.execute("""SELECT name, segment, industry, ltv, deals_count, since_year
        FROM customers WHERE churn_risk='High' ORDER BY ltv DESC LIMIT 5""").fetchall()
    top = conn.execute(
        "SELECT name, segment, ltv, deals_count, status FROM customers ORDER BY ltv DESC LIMIT 5"
    ).fetchall()
    avg_ltv = conn.execute("SELECT AVG(ltv) as avg_ltv FROM customers").fetchone()
    conn.close()
    return {
        "avg_ltv": round(avg_ltv["avg_ltv"], 2),
        "churn_summary": [dict(r) for r in churn],
        "at_risk_accounts": [dict(r) for r in at_risk],
        "top_customers_by_ltv": [dict(r) for r in top],
    }


# ── TABLE 4: Team ─────────────────────────────────────────────────────────────
def get_team_stats() -> Dict[str, Any]:
    conn = _conn()
    depts = conn.execute("""SELECT department, COUNT(*) as headcount, SUM(salary) as salary_burn,
        AVG(performance) as avg_perf, AVG(tenure_years) as avg_tenure
        FROM team WHERE status='Active' GROUP BY department""").fetchall()
    total = conn.execute("SELECT SUM(salary) as total FROM team WHERE status='Active'").fetchone()
    low = conn.execute(
        "SELECT name, department, role, performance FROM team WHERE performance < 4.0 AND status='Active'"
    ).fetchall()
    conn.close()
    return {
        "total_headcount": sum(r["headcount"] for r in depts),
        "total_annual_payroll": total["total"] or 0,
        "by_department": [dict(r) for r in depts],
        "low_performers": [dict(r) for r in low],
    }


# ── TABLE 5: Decisions ────────────────────────────────────────────────────────
def get_decision_history(limit: int = 25) -> list:
    conn = _conn()
    rows = conn.execute("SELECT * FROM decisions ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── TABLE 6: Products ─────────────────────────────────────────────────────────
def get_product_metrics() -> Dict[str, Any]:
    conn = _conn()
    by_cat = conn.execute("""SELECT category, COUNT(*) as count, SUM(revenue_ytd) as revenue,
        AVG(margin_pct) as avg_margin, SUM(units_sold_ytd) as total_units
        FROM products WHERE status='Active' GROUP BY category ORDER BY revenue DESC""").fetchall()
    top = conn.execute(
        "SELECT name, category, unit_price, margin_pct, units_sold_ytd, revenue_ytd FROM products ORDER BY revenue_ytd DESC LIMIT 5"
    ).fetchall()
    totals = conn.execute("SELECT SUM(revenue_ytd) as total_rev, AVG(margin_pct) as avg_margin FROM products WHERE status='Active'").fetchone()
    low_margin = conn.execute("SELECT name, category, margin_pct, revenue_ytd FROM products WHERE margin_pct < 55 AND status='Active'").fetchall()
    conn.close()
    return {
        "total_product_revenue_ytd": totals["total_rev"] or 0,
        "avg_portfolio_margin": round(totals["avg_margin"] or 0, 1),
        "by_category": [dict(r) for r in by_cat],
        "top_products": [dict(r) for r in top],
        "low_margin_products": [dict(r) for r in low_margin],
    }


# ── TABLE 7: Inventory ────────────────────────────────────────────────────────
def get_inventory_status() -> Dict[str, Any]:
    conn = _conn()
    critical = conn.execute(
        "SELECT * FROM inventory WHERE status='Critical' ORDER BY days_of_supply"
    ).fetchall()
    low = conn.execute(
        "SELECT * FROM inventory WHERE status='Low' ORDER BY days_of_supply"
    ).fetchall()
    ok = conn.execute("SELECT COUNT(*) as c FROM inventory WHERE status='OK'").fetchone()
    avg_supply = conn.execute("SELECT AVG(days_of_supply) as avg FROM inventory WHERE days_of_supply IS NOT NULL").fetchone()
    conn.close()
    return {
        "critical_items": [dict(r) for r in critical],
        "low_items": [dict(r) for r in low],
        "ok_count": ok["c"],
        "avg_days_of_supply": round(avg_supply["avg"] or 0, 1),
        "needs_immediate_reorder": len(critical),
    }


# ── TABLE 8: Campaigns ────────────────────────────────────────────────────────
def get_campaign_performance() -> Dict[str, Any]:
    conn = _conn()
    by_channel = conn.execute("""SELECT channel, COUNT(*) as count, SUM(spend) as total_spend,
        SUM(leads_generated) as total_leads, SUM(conversions) as total_conv,
        SUM(revenue_attributed) as total_revenue, AVG(roi_pct) as avg_roi
        FROM campaigns WHERE roi_pct > 0 GROUP BY channel ORDER BY total_revenue DESC""").fetchall()
    top = conn.execute(
        "SELECT name, channel, spend, conversions, revenue_attributed, roi_pct FROM campaigns WHERE roi_pct > 0 ORDER BY roi_pct DESC LIMIT 5"
    ).fetchall()
    totals = conn.execute(
        "SELECT SUM(budget) as budget, SUM(spend) as spend, SUM(leads_generated) as leads, "
        "SUM(conversions) as conv, SUM(revenue_attributed) as revenue FROM campaigns"
    ).fetchone()
    conn.close()
    overall_roi = round((totals["revenue"] - totals["spend"]) / totals["spend"] * 100, 1) if totals["spend"] else 0
    return {
        "total_budget": totals["budget"] or 0,
        "total_spend": totals["spend"] or 0,
        "total_leads": totals["leads"] or 0,
        "total_conversions": totals["conv"] or 0,
        "total_revenue_attributed": totals["revenue"] or 0,
        "overall_roi_pct": overall_roi,
        "by_channel": [dict(r) for r in by_channel],
        "top_campaigns_by_roi": [dict(r) for r in top],
    }


# ── TABLE 9: Support Tickets ──────────────────────────────────────────────────
def get_support_metrics() -> Dict[str, Any]:
    conn = _conn()
    summary = conn.execute(
        "SELECT COUNT(*) as total, AVG(resolution_days) as avg_days, AVG(csat_score) as avg_csat "
        "FROM support_tickets WHERE status='Closed' AND resolution_days IS NOT NULL"
    ).fetchone()
    by_cat = conn.execute(
        "SELECT category, COUNT(*) as count, AVG(resolution_days) as avg_days, AVG(csat_score) as avg_csat "
        "FROM support_tickets GROUP BY category ORDER BY count DESC"
    ).fetchall()
    open_t = conn.execute(
        "SELECT COUNT(*) as c, priority FROM support_tickets WHERE status IN ('Open','In Progress') GROUP BY priority"
    ).fetchall()
    critical_open = conn.execute(
        "SELECT customer_name, category, opened_date FROM support_tickets WHERE priority='Critical' AND status IN ('Open','In Progress')"
    ).fetchall()
    conn.close()
    return {
        "resolved_count": summary["total"] or 0,
        "avg_resolution_days": round(summary["avg_days"] or 0, 1),
        "avg_csat": round(summary["avg_csat"] or 0, 1),
        "by_category": [dict(r) for r in by_cat],
        "open_by_priority": [dict(r) for r in open_t],
        "critical_open": [dict(r) for r in critical_open],
    }


# ── TABLE 10: Suppliers ───────────────────────────────────────────────────────
def get_supplier_health() -> Dict[str, Any]:
    conn = _conn()
    all_s = conn.execute("SELECT * FROM suppliers ORDER BY reliability_score DESC").fetchall()
    risky = conn.execute("SELECT * FROM suppliers WHERE risk_level='High'").fetchall()
    total_spend = conn.execute("SELECT SUM(annual_spend) as total FROM suppliers").fetchone()
    avg_reliability = conn.execute("SELECT AVG(reliability_score) as avg FROM suppliers").fetchone()
    conn.close()
    return {
        "total_annual_supplier_spend": total_spend["total"] or 0,
        "avg_reliability_score": round(avg_reliability["avg"] or 0, 1),
        "high_risk_suppliers": [dict(r) for r in risky],
        "all_suppliers": [dict(r) for r in all_s],
    }


# ── TABLE 11: Expenses ────────────────────────────────────────────────────────
def get_expense_breakdown() -> Dict[str, Any]:
    conn = _conn()
    recent = conn.execute("SELECT * FROM expenses ORDER BY month DESC LIMIT 6").fetchall()
    conn.close()
    if not recent:
        return {}
    latest = dict(recent[0])
    avg_total = sum(r["total"] for r in recent) / len(recent)
    # Breakdown percentages for latest month
    cats = ["salaries", "cloud_infrastructure", "marketing_spend", "office_rent",
            "software_tools", "operations", "r_and_d", "travel", "other"]
    breakdown_pct = {c: round(latest.get(c, 0) / latest["total"] * 100, 1) for c in cats}
    return {
        "latest_month": latest["month"],
        "latest_total": latest["total"],
        "avg_monthly_expenses_6m": round(avg_total, 0),
        "breakdown_latest": breakdown_pct,
        "largest_cost_category": max(breakdown_pct, key=breakdown_pct.get),
        "monthly_trend": [{"month": r["month"], "total": r["total"]} for r in reversed(recent)],
    }


# ── TABLE 12: KPIs ────────────────────────────────────────────────────────────
def get_kpi_summary() -> Dict[str, Any]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM kpis ORDER BY id").fetchall()
    conn.close()
    if not rows:
        return {}
    latest, first = dict(rows[-1]), dict(rows[0])
    arr_growth = round((latest["arr"] - first["arr"]) / first["arr"] * 100, 1) if first["arr"] else 0
    nps_change = latest["nps_score"] - first["nps_score"]
    churn_change = round(latest["churn_rate_pct"] - first["churn_rate_pct"], 2)
    return {
        "latest_period": latest["period"],
        "latest_mrr": latest["mrr"],
        "latest_arr": latest["arr"],
        "latest_churn_pct": latest["churn_rate_pct"],
        "latest_nps": latest["nps_score"],
        "latest_cac": latest["customer_acquisition_cost"],
        "latest_win_rate": latest["win_rate_pct"],
        "arr_growth_pct_total": arr_growth,
        "nps_change": nps_change,
        "churn_improvement": churn_change,  # negative = improved
        "all_periods": [dict(r) for r in rows],
    }


# ── TABLE 13: Contracts ───────────────────────────────────────────────────────
def get_contracts_summary() -> Dict[str, Any]:
    conn = _conn()
    all_c = conn.execute("SELECT * FROM contracts ORDER BY arr DESC").fetchall()
    at_risk = conn.execute(
        "SELECT * FROM contracts WHERE status='At Risk' ORDER BY arr DESC"
    ).fetchall()
    totals = conn.execute("SELECT SUM(arr) as total_arr, AVG(health_score) as avg_health FROM contracts").fetchone()
    expansion = conn.execute(
        "SELECT customer_name, arr, expansion_potential FROM contracts WHERE expansion_potential='High' ORDER BY arr DESC"
    ).fetchall()
    conn.close()
    return {
        "total_arr": totals["total_arr"] or 0,
        "avg_health_score": round(totals["avg_health"] or 0, 1),
        "at_risk_contracts": [dict(r) for r in at_risk],
        "at_risk_arr": sum(r["arr"] for r in at_risk),
        "expansion_opportunities": [dict(r) for r in expansion],
        "all_contracts": [dict(r) for r in all_c],
    }


# ── Smart Context Builder for LLM ─────────────────────────────────────────────
def get_context_for_query(intent_keywords: list) -> str:
    """
    Builds a rich context string by pulling relevant tables based on intent keywords.
    """
    kw = [k.lower() for k in intent_keywords]
    parts = []

    # Always include financial snapshot
    fin = get_financial_summary()
    if fin:
        parts.append(
            f"[FINANCIALS] {fin['latest_month']}: Revenue ${fin['latest_revenue']:,.0f}, "
            f"Profit ${fin['latest_profit']:,.0f} ({fin['avg_profit_margin_pct']}% avg margin), "
            f"Trend: {fin['revenue_trend']}. 6M total profit ${fin['total_profit_6m']:,.0f}."
        )

    # Sales / pipeline
    if any(w in kw for w in ["sale","deal","pipeline","revenue","customer","client","close","win","quota"]):
        p = get_deal_pipeline()
        parts.append(
            f"[PIPELINE] Open ${p['open_pipeline_value']:,.0f} across {p['open_deal_count']} deals. "
            f"Closed-Won ${p['closed_won_value']:,.0f}. "
            f"Top deals: {', '.join([d['customer_name']+' $'+str(int(d['value'])) for d in p['top_open_deals'][:3]])}."
        )

    # Customer / churn / retention
    if any(w in kw for w in ["customer","churn","retention","risk","ltv","account","client"]):
        h = get_customer_health()
        parts.append(
            f"[CUSTOMERS] Avg LTV ${h['avg_ltv']:,.0f}. "
            f"High-churn-risk: {', '.join([a['name'] for a in h['at_risk_accounts']])}. "
            f"Top by LTV: {', '.join([c['name'] for c in h['top_customers_by_ltv'][:3]])}."
        )

    # Contracts / ARR / renewal
    if any(w in kw for w in ["contract","renew","arr","subscription","mrr","recurring"]):
        c = get_contracts_summary()
        parts.append(
            f"[CONTRACTS] Total ARR ${c['total_arr']:,.0f}, avg health {c['avg_health_score']}/100. "
            f"At-risk ARR ${c['at_risk_arr']:,.0f} across {len(c['at_risk_contracts'])} contracts. "
            f"Expansion opportunities: {', '.join([e['customer_name'] for e in c['expansion_opportunities'][:3]])}."
        )

    # Hiring / HR / team
    if any(w in kw for w in ["hire","hiring","team","employee","staff","hr","salary","headcount","talent","people","recruit"]):
        t = get_team_stats()
        dept_str = ", ".join([f"{d['department']} ({d['headcount']}p, {round(d['avg_perf'],1)} perf)" for d in t["by_department"]])
        parts.append(
            f"[TEAM] {t['total_headcount']} employees, annual payroll ${t['total_annual_payroll']:,.0f}. "
            f"Depts: {dept_str}. Low performers: {len(t['low_performers'])}."
        )

    # KPIs / metrics / growth
    if any(w in kw for w in ["kpi","metric","growth","nps","cac","churn","win rate","velocity"]):
        k = get_kpi_summary()
        if k:
            parts.append(
                f"[KPIs] {k['latest_period']}: ARR ${k['latest_arr']:,.0f} ({k['arr_growth_pct_total']}% growth), "
                f"Churn {k['latest_churn_pct']}%, NPS {k['latest_nps']}, "
                f"CAC ${k['latest_cac']:,.0f}, Win rate {k['latest_win_rate']}%."
            )

    # Products / SKUs / margin
    if any(w in kw for w in ["product","sku","price","launch","feature","margin","portfolio","line"]):
        pr = get_product_metrics()
        low_m = [p["name"] for p in pr["low_margin_products"]]
        parts.append(
            f"[PRODUCTS] Portfolio revenue YTD ${pr['total_product_revenue_ytd']:,.0f}, avg margin {pr['avg_portfolio_margin']}%. "
            f"Top product: {pr['top_products'][0]['name'] if pr['top_products'] else 'N/A'}. "
            f"Low-margin items: {', '.join(low_m) if low_m else 'None'}."
        )

    # Marketing / campaigns / CAC
    if any(w in kw for w in ["marketing","campaign","leads","ads","seo","email","content","brand","channel"]):
        camp = get_campaign_performance()
        parts.append(
            f"[MARKETING] Total spend ${camp['total_spend']:,.0f}, overall ROI {camp['overall_roi_pct']}%. "
            f"{camp['total_leads']:,} leads generated, {camp['total_conversions']} conversions. "
            f"Best channel: {camp['by_channel'][0]['channel'] if camp['by_channel'] else 'N/A'}."
        )

    # Support / CSAT / tickets
    if any(w in kw for w in ["support","ticket","csat","complaint","issue","bug","customer service"]):
        sup = get_support_metrics()
        crit_open = len(sup["critical_open"])
        parts.append(
            f"[SUPPORT] Avg resolution {sup['avg_resolution_days']} days, CSAT {sup['avg_csat']}/5. "
            f"{crit_open} critical tickets currently open. "
            f"Top category: {sup['by_category'][0]['category'] if sup['by_category'] else 'N/A'}."
        )

    # Suppliers / vendors / cost
    if any(w in kw for w in ["supplier","vendor","procurement","logistics","aws","cloud","outsource","partner"]):
        sup = get_supplier_health()
        risky = [r["name"] for r in sup["high_risk_suppliers"]]
        parts.append(
            f"[SUPPLIERS] Annual supplier spend ${sup['total_annual_supplier_spend']:,.0f}, "
            f"avg reliability {sup['avg_reliability_score']}/100. "
            f"High-risk suppliers: {', '.join(risky) if risky else 'None'}."
        )

    # Inventory / stock
    if any(w in kw for w in ["inventory","stock","warehouse","supply","hardware","reorder","shortage"]):
        inv = get_inventory_status()
        parts.append(
            f"[INVENTORY] {inv['needs_immediate_reorder']} critical items need reorder, "
            f"{len(inv['low_items'])} low. Avg supply {inv['avg_days_of_supply']} days. "
            f"Critical: {', '.join([i['product_name'] for i in inv['critical_items']][:3]) if inv['critical_items'] else 'None'}."
        )

    # Expenses / costs / burn rate
    if any(w in kw for w in ["expense","cost","burn","budget","spend","overhead","office","rent"]):
        exp = get_expense_breakdown()
        if exp:
            parts.append(
                f"[EXPENSES] {exp['latest_month']} total expenses ${exp['latest_total']:,.0f}. "
                f"Largest cost: {exp['largest_cost_category']} ({exp['breakdown_latest'].get(exp['largest_cost_category'],0)}%). "
                f"6M avg ${exp['avg_monthly_expenses_6m']:,.0f}/month."
            )

    # Expansion / operations
    if any(w in kw for w in ["expand","expansion","branch","city","region","office","open","capacity","operations"]):
        fin = get_financial_summary()
        t = get_team_stats()
        k = get_kpi_summary()
        ops_size = next((d['headcount'] for d in t['by_department'] if d['department']=='Operations'), 0)
        parts.append(
            f"[OPERATIONS] Revenue {fin.get('revenue_trend','stable')}. "
            f"Ops team: {ops_size} people. "
            f"Current ARR ${k.get('latest_arr',0):,.0f}, CAC ${k.get('latest_cac',0):,.0f}."
            if k else
            f"[OPERATIONS] Revenue {fin.get('revenue_trend','stable')}. Ops team: {ops_size} people."
        )

    return "\n".join(parts) if parts else "[CRM] General business context available across 13 datasets."
