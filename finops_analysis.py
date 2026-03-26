"""
finops_analysis.py
Core analysis engine for the Cloud FinOps Governance Dashboard.
Produces spend attribution, waste identification, and ROI calculations
that map infrastructure costs to business workflow outcomes.
"""

import pandas as pd
import numpy as np


def load_data(cost_path="data/aws_costs.csv", workflow_path="data/workflow_metrics.csv"):
    costs     = pd.read_csv(cost_path)
    workflows = pd.read_csv(workflow_path)
    return costs, workflows


# ── SPEND ATTRIBUTION ────────────────────────────────────────────────────────

def monthly_spend_trend(costs: pd.DataFrame) -> pd.DataFrame:
    """Total spend per month with MoM delta."""
    monthly = (
        costs.groupby("month")["total_cost_usd"]
        .sum()
        .reset_index()
        .rename(columns={"total_cost_usd": "total_spend"})
    )
    monthly["mom_delta"]   = monthly["total_spend"].diff()
    monthly["mom_pct"]     = monthly["total_spend"].pct_change().round(4)
    return monthly


def spend_by_business_unit(costs: pd.DataFrame) -> pd.DataFrame:
    """Spend attribution per business unit with waste breakdown."""
    bu = costs.groupby("business_unit").agg(
        total_spend   =("total_cost_usd",  "sum"),
        total_waste   =("waste_amount_usd", "sum"),
        optimized_cost=("optimized_cost",   "sum"),
    ).reset_index()
    bu["waste_pct"]      = (bu["total_waste"] / bu["total_spend"]).round(4)
    bu["potential_save"] = bu["total_waste"].round(2)
    return bu.sort_values("total_spend", ascending=False)


def spend_by_service(costs: pd.DataFrame) -> pd.DataFrame:
    """Which AWS services are driving the most cost."""
    svc = costs.groupby("aws_service").agg(
        total_spend=("total_cost_usd",   "sum"),
        total_waste=("waste_amount_usd", "sum"),
    ).reset_index()
    svc["waste_pct"]   = (svc["total_waste"] / svc["total_spend"]).round(4)
    svc["spend_share"] = (svc["total_spend"] / svc["total_spend"].sum()).round(4)
    return svc.sort_values("total_spend", ascending=False)


def environment_waste_analysis(costs: pd.DataFrame) -> pd.DataFrame:
    """Dev/staging environments often carry disproportionate waste."""
    env = costs.groupby("environment").agg(
        total_spend=("total_cost_usd",   "sum"),
        total_waste=("waste_amount_usd", "sum"),
    ).reset_index()
    env["waste_pct"] = (env["total_waste"] / env["total_spend"]).round(4)
    return env.sort_values("waste_pct", ascending=False)


# ── ROI & BUSINESS VALUE ─────────────────────────────────────────────────────

def workflow_roi(costs: pd.DataFrame, workflows: pd.DataFrame) -> pd.DataFrame:
    """
    Core value mapping: maps infrastructure spend per BU to workflow outcomes.
    This is the CFO-level view — cost per transaction and FTE efficiency.
    """
    cost_by_bu = costs.groupby("business_unit")["total_cost_usd"].sum().reset_index()
    cost_by_bu.columns = ["business_unit", "infra_spend"]

    wf_by_bu = workflows.groupby("business_unit").agg(
        total_runs     =("total_runs",       "sum"),
        fte_hours_saved=("fte_hours_saved",  "sum"),
        avg_success    =("success_rate",     "mean"),
    ).reset_index()

    roi = pd.merge(cost_by_bu, wf_by_bu, on="business_unit")
    roi["cost_per_run"]        = (roi["infra_spend"] / roi["total_runs"]).round(4)
    roi["cost_per_fte_hour"]   = (roi["infra_spend"] / roi["fte_hours_saved"]).round(2)
    roi["fte_dollar_value"]    = (roi["fte_hours_saved"] * 65).round(0)  # $65/hr blended rate
    roi["net_roi_usd"]         = (roi["fte_dollar_value"] - roi["infra_spend"]).round(0)
    roi["roi_multiple"]        = (roi["fte_dollar_value"] / roi["infra_spend"]).round(2)
    roi["avg_success_pct"]     = (roi["avg_success"] * 100).round(1)
    return roi.sort_values("net_roi_usd", ascending=False)


# ── OPTIMIZATION RECOMMENDATIONS ─────────────────────────────────────────────

def rightsizing_recommendations(costs: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies the top rightsizing opportunities by BU + service combination.
    Mirrors what a cloud architect would surface in a FinOps review.
    """
    recs = costs.groupby(["business_unit", "aws_service", "environment"]).agg(
        avg_monthly_spend=("total_cost_usd",   "mean"),
        avg_waste        =("waste_amount_usd", "mean"),
    ).reset_index()
    recs["waste_pct"]        = (recs["avg_waste"] / recs["avg_monthly_spend"]).round(4)
    recs["annual_save_opp"]  = (recs["avg_waste"] * 12).round(0)
    recs["priority"]         = pd.cut(
        recs["waste_pct"],
        bins=[0, 0.15, 0.25, 1.0],
        labels=["Low", "Medium", "High"]
    )
    return (
        recs[recs["waste_pct"] > 0.15]
        .sort_values("annual_save_opp", ascending=False)
        .head(15)
        .reset_index(drop=True)
    )


# ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────────

def executive_summary(costs: pd.DataFrame, workflows: pd.DataFrame) -> dict:
    """
    Single-call summary for QBR slide or exec dashboard header.
    Returns the key metrics a CFO or VP of Engineering cares about.
    """
    roi = workflow_roi(costs, workflows)

    total_spend      = costs["total_cost_usd"].sum()
    total_waste      = costs["waste_amount_usd"].sum()
    total_fte_saved  = workflows["fte_hours_saved"].sum()
    total_runs       = workflows["total_runs"].sum()
    avg_success      = workflows["success_rate"].mean()

    return {
        "total_infra_spend_usd":    round(total_spend, 0),
        "recoverable_waste_usd":    round(total_waste, 0),
        "waste_percentage":         round(total_waste / total_spend * 100, 1),
        "total_workflow_runs":      int(total_runs),
        "fte_hours_saved":          round(total_fte_saved, 0),
        "fte_dollar_value_usd":     round(total_fte_saved * 65, 0),
        "net_roi_usd":              round(total_fte_saved * 65 - total_spend, 0),
        "overall_roi_multiple":     round((total_fte_saved * 65) / total_spend, 2),
        "avg_workflow_success_pct": round(avg_success * 100, 1),
        "cost_per_transaction_usd": round(total_spend / total_runs, 4),
    }


if __name__ == "__main__":
    costs, workflows = load_data()

    print("=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)
    summary = executive_summary(costs, workflows)
    for k, v in summary.items():
        label = k.replace("_", " ").title()
        if "usd" in k:
            print(f"  {label:<35} ${v:>12,.0f}")
        elif "pct" in k or "percentage" in k or "multiple" in k:
            print(f"  {label:<35} {v:>12}")
        else:
            print(f"  {label:<35} {v:>12,}")

    print("\n" + "=" * 60)
    print("SPEND BY BUSINESS UNIT")
    print("=" * 60)
    bu = spend_by_business_unit(costs)
    print(bu[["business_unit", "total_spend", "total_waste", "waste_pct", "potential_save"]].to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP RIGHTSIZING OPPORTUNITIES")
    print("=" * 60)
    recs = rightsizing_recommendations(costs)
    print(recs[["business_unit", "aws_service", "environment", "waste_pct", "annual_save_opp", "priority"]].to_string(index=False))
