"""
dashboard.py
Generates the full FinOps Governance Dashboard — 6 publication-quality charts
saved to output/charts/ and a combined PNG executive report.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import os
import warnings
warnings.filterwarnings("ignore")

from finops_analysis import (
    load_data, monthly_spend_trend, spend_by_business_unit,
    spend_by_service, workflow_roi, rightsizing_recommendations,
    executive_summary, environment_waste_analysis
)

# ── STYLE ────────────────────────────────────────────────────────────────────
PALETTE = {
    "primary":   "#0B4F8A",
    "secondary": "#1A77C9",
    "accent":    "#F5A623",
    "danger":    "#C0392B",
    "success":   "#1E8449",
    "neutral":   "#7F8C8D",
    "bg":        "#F8F9FA",
    "white":     "#FFFFFF",
    "text":      "#1A1A2E",
    "grid":      "#E8ECF0",
}

BU_COLORS = [
    "#0B4F8A", "#1A77C9", "#2E86C1", "#5DADE2", "#85C1E9", "#AED6F1"
]

plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          10,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "axes.grid":          True,
    "grid.color":         PALETTE["grid"],
    "grid.linewidth":     0.6,
    "axes.facecolor":     PALETTE["white"],
    "figure.facecolor":   PALETTE["bg"],
    "text.color":         PALETTE["text"],
    "axes.labelcolor":    PALETTE["text"],
    "xtick.color":        PALETTE["text"],
    "ytick.color":        PALETTE["text"],
})

os.makedirs("output/charts", exist_ok=True)


def fmt_dollar(x, pos=None):
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:.0f}"


# ── CHART 1: Monthly Spend Trend ─────────────────────────────────────────────
def chart_monthly_trend(costs):
    monthly = monthly_spend_trend(costs)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor(PALETTE["white"])
    ax.set_facecolor(PALETTE["white"])

    ax.fill_between(monthly["month"], monthly["total_spend"],
                    alpha=0.12, color=PALETTE["primary"])
    ax.plot(monthly["month"], monthly["total_spend"],
            color=PALETTE["primary"], linewidth=2.5, marker="o",
            markersize=6, markerfacecolor=PALETTE["white"],
            markeredgecolor=PALETTE["primary"], markeredgewidth=2)

    # Annotate last point
    last = monthly.iloc[-1]
    ax.annotate(f'${last["total_spend"]/1000:.0f}K',
                xy=(last["month"], last["total_spend"]),
                xytext=(0, 14), textcoords="offset points",
                ha="center", fontsize=9, fontweight="bold",
                color=PALETTE["primary"])

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    ax.set_xlabel("Month", labelpad=8)
    ax.set_ylabel("Total AWS Spend (USD)", labelpad=8)
    ax.set_title("Monthly Cloud Infrastructure Spend — 2024", fontsize=13,
                 fontweight="bold", pad=14, loc="left")
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig("output/charts/01_monthly_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 01_monthly_trend.png")


# ── CHART 2: Spend by Business Unit (horizontal bar) ─────────────────────────
def chart_by_bu(costs):
    bu = spend_by_business_unit(costs).sort_values("total_spend")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(PALETTE["white"])
    ax.set_facecolor(PALETTE["white"])

    bars = ax.barh(bu["business_unit"], bu["total_spend"],
                   color=BU_COLORS[::-1], edgecolor="none", height=0.55)
    ax.barh(bu["business_unit"], bu["total_waste"],
            color=PALETTE["danger"], alpha=0.5, edgecolor="none", height=0.55,
            label="Recoverable Waste")

    for bar, (_, row) in zip(bars, bu.iterrows()):
        ax.text(bar.get_width() + 800, bar.get_y() + bar.get_height() / 2,
                f'${row["total_spend"]/1000:.0f}K  |  waste {row["waste_pct"]*100:.0f}%',
                va="center", fontsize=8.5, color=PALETTE["text"])

    ax.set_xlabel("Annual AWS Spend (USD)", labelpad=8)
    ax.set_title("Infrastructure Spend Attribution by Business Unit", fontsize=13,
                 fontweight="bold", pad=14, loc="left")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    ax.legend(loc="lower right", framealpha=0)
    ax.set_xlim(0, bu["total_spend"].max() * 1.35)
    ax.grid(axis="x"); ax.grid(axis="y", alpha=0)
    ax.spines["bottom"].set_visible(False)
    plt.tight_layout()
    plt.savefig("output/charts/02_spend_by_bu.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 02_spend_by_bu.png")


# ── CHART 3: Service Breakdown (donut) ───────────────────────────────────────
def chart_service_donut(costs):
    svc = spend_by_service(costs).sort_values("total_spend", ascending=False)
    top5   = svc.head(5)
    other  = pd.DataFrame([{
        "aws_service": "Other Services",
        "total_spend": svc.iloc[5:]["total_spend"].sum()
    }])
    data = pd.concat([top5[["aws_service", "total_spend"]], other], ignore_index=True)

    colors = [PALETTE["primary"], PALETTE["secondary"], "#2E86C1",
              "#5DADE2", "#85C1E9", PALETTE["neutral"]]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor(PALETTE["white"])
    wedges, texts, autotexts = ax.pie(
        data["total_spend"], labels=None,
        autopct="%1.1f%%", startangle=90,
        colors=colors, pctdistance=0.78,
        wedgeprops={"width": 0.52, "edgecolor": "white", "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontsize(8); at.set_color("white"); at.set_fontweight("bold")

    ax.legend(data["aws_service"], loc="center left", bbox_to_anchor=(0.85, 0.5),
              framealpha=0, fontsize=9)
    centre = plt.Circle((0, 0), 0.35, color="white")
    ax.add_patch(centre)
    total = data["total_spend"].sum()
    ax.text(0, 0.06, fmt_dollar(total), ha="center", va="center",
            fontsize=13, fontweight="bold", color=PALETTE["primary"])
    ax.text(0, -0.12, "Total Spend", ha="center", va="center",
            fontsize=8.5, color=PALETTE["neutral"])
    ax.set_title("AWS Service Cost Distribution", fontsize=13,
                 fontweight="bold", pad=14, loc="left", x=-0.05)
    plt.tight_layout()
    plt.savefig("output/charts/03_service_breakdown.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 03_service_breakdown.png")


# ── CHART 4: ROI — Cost vs Value Delivered ───────────────────────────────────
def chart_roi(costs, workflows):
    roi = workflow_roi(costs, workflows).sort_values("net_roi_usd", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(PALETTE["white"])
    ax.set_facecolor(PALETTE["white"])

    x      = range(len(roi))
    width  = 0.35
    bars1  = ax.bar([i - width/2 for i in x], roi["infra_spend"],
                    width, label="Infrastructure Spend", color=PALETTE["secondary"],
                    alpha=0.85, edgecolor="none")
    bars2  = ax.bar([i + width/2 for i in x], roi["fte_dollar_value"],
                    width, label="FTE Value Delivered ($65/hr)", color=PALETTE["success"],
                    alpha=0.85, edgecolor="none")

    ax.set_xticks(list(x))
    ax.set_xticklabels(roi["business_unit"], rotation=20, ha="right", fontsize=8.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    ax.set_title("Infrastructure Spend vs. Business Value Delivered (ROI View)", fontsize=13,
                 fontweight="bold", pad=14, loc="left")
    ax.set_ylabel("USD", labelpad=8)
    ax.legend(framealpha=0)

    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                fmt_dollar(bar.get_height()),
                ha="center", va="bottom", fontsize=7.5, color=PALETTE["success"],
                fontweight="bold")
    plt.tight_layout()
    plt.savefig("output/charts/04_roi_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 04_roi_comparison.png")


# ── CHART 5: Rightsizing Opportunities ───────────────────────────────────────
def chart_rightsizing(costs):
    recs = rightsizing_recommendations(costs).head(10)
    recs["label"] = recs["business_unit"].str.split().str[0] + " / " + recs["aws_service"]

    color_map = {"High": PALETTE["danger"], "Medium": PALETTE["accent"], "Low": PALETTE["neutral"]}
    colors = recs["priority"].map(color_map).tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(PALETTE["white"])
    ax.set_facecolor(PALETTE["white"])

    bars = ax.barh(recs["label"], recs["annual_save_opp"],
                   color=colors, edgecolor="none", height=0.6)
    for bar, (_, row) in zip(bars, recs.iterrows()):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
                f'${row["annual_save_opp"]:,.0f}/yr  ({row["waste_pct"]*100:.0f}% waste)',
                va="center", fontsize=8, color=PALETTE["text"])

    ax.set_xlabel("Estimated Annual Savings (USD)", labelpad=8)
    ax.set_title("Top Rightsizing Opportunities", fontsize=13,
                 fontweight="bold", pad=14, loc="left")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_dollar))
    ax.set_xlim(0, recs["annual_save_opp"].max() * 1.5)
    ax.grid(axis="x"); ax.grid(axis="y", alpha=0)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=PALETTE["danger"],  label="High Priority"),
        Patch(facecolor=PALETTE["accent"],  label="Medium Priority"),
        Patch(facecolor=PALETTE["neutral"], label="Low Priority"),
    ]
    ax.legend(handles=legend_elements, framealpha=0, loc="lower right")
    plt.tight_layout()
    plt.savefig("output/charts/05_rightsizing.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 05_rightsizing.png")


# ── CHART 6: Executive KPI Summary Card ──────────────────────────────────────
def chart_exec_summary(costs, workflows):
    summary = executive_summary(costs, workflows)
    fig = plt.figure(figsize=(12, 4))
    fig.patch.set_facecolor(PALETTE["primary"])

    kpis = [
        ("Total Cloud Spend",         f'${summary["total_infra_spend_usd"]/1000:.0f}K',   PALETTE["white"]),
        ("Recoverable Waste",         f'${summary["recoverable_waste_usd"]/1000:.0f}K\n({summary["waste_percentage"]}%)', "#F5A623"),
        ("FTE Hours Saved",           f'{summary["fte_hours_saved"]/1000:.1f}K hrs',       "#85C1E9"),
        ("FTE Dollar Value",          f'${summary["fte_dollar_value_usd"]/1000:.0f}K',     "#1E8449"),
        ("Net ROI",                   f'{summary["overall_roi_multiple"]}x',               "#A9DFBF"),
        ("Avg Workflow Success",      f'{summary["avg_workflow_success_pct"]}%',           PALETTE["white"]),
    ]

    for i, (label, value, color) in enumerate(kpis):
        ax = fig.add_axes([i/6 + 0.01, 0.08, 1/6 - 0.02, 0.84])
        ax.set_facecolor("white" if i % 2 == 0 else "#0D4075")
        ax.axis("off")
        ax.text(0.5, 0.62, value, transform=ax.transAxes,
                ha="center", va="center", fontsize=18, fontweight="bold",
                color=PALETTE["primary"] if i % 2 == 0 else color)
        ax.text(0.5, 0.22, label, transform=ax.transAxes,
                ha="center", va="center", fontsize=8.5,
                color=PALETTE["neutral"] if i % 2 == 0 else "#AED6F1")

    fig.text(0.5, 0.97, "Cloud FinOps Governance Dashboard  |  FY 2024 Executive Summary",
             ha="center", va="top", fontsize=11, fontweight="bold",
             color="white", transform=fig.transFigure)
    plt.savefig("output/charts/06_exec_summary.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["primary"])
    plt.close()
    print("  Saved: 06_exec_summary.png")


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading data...")
    costs, workflows = load_data()

    print("Generating charts...")
    chart_monthly_trend(costs)
    chart_by_bu(costs)
    chart_service_donut(costs)
    chart_roi(costs, workflows)
    chart_rightsizing(costs)
    chart_exec_summary(costs, workflows)

    print("\nAll charts saved to output/charts/")
