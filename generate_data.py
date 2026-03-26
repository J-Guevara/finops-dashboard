"""
generate_data.py
Generates realistic synthetic AWS cost data for an enterprise RPA/automation environment.
Simulates 12 months of spend across compute, storage, and network for 6 business units.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

BUSINESS_UNITS = [
    "Finance Automation",
    "HR Operations",
    "Supply Chain",
    "Customer Service",
    "IT Infrastructure",
    "Compliance & Risk",
]

SERVICES = {
    "EC2 Compute":     {"base": 4200, "volatility": 0.18},
    "EKS Cluster":     {"base": 3100, "volatility": 0.12},
    "RDS Database":    {"base": 1800, "volatility": 0.08},
    "S3 Storage":      {"base":  620, "volatility": 0.05},
    "Lambda":          {"base":  340, "volatility": 0.25},
    "Data Transfer":   {"base":  480, "volatility": 0.15},
    "CloudWatch":      {"base":  190, "volatility": 0.06},
    "Load Balancer":   {"base":  280, "volatility": 0.09},
}

BU_WEIGHTS = {
    "Finance Automation":  0.28,
    "HR Operations":       0.12,
    "Supply Chain":        0.22,
    "Customer Service":    0.18,
    "IT Infrastructure":   0.10,
    "Compliance & Risk":   0.10,
}

WORKFLOW_MAP = {
    "Finance Automation":  ["Invoice Processing", "GL Reconciliation", "Expense Approval", "FP&A Reporting"],
    "HR Operations":       ["Onboarding Automation", "Payroll Sync", "Benefits Enrollment"],
    "Supply Chain":        ["PO Processing", "Inventory Sync", "Vendor Matching", "Shipment Tracking"],
    "Customer Service":    ["Ticket Routing", "Refund Processing", "SLA Monitoring"],
    "IT Infrastructure":   ["Patch Deployment", "Access Provisioning", "Incident Response"],
    "Compliance & Risk":   ["Audit Log Collection", "SOC2 Evidence Packaging", "GDPR Data Mapping"],
}


def generate_monthly_costs():
    records = []
    start = datetime(2024, 1, 1)

    for month_offset in range(12):
        month_date = start + timedelta(days=30 * month_offset)
        month_str  = month_date.strftime("%Y-%m")

        # Natural growth trend: ~2% MoM with a summer dip
        trend = 1 + (month_offset * 0.02)
        season = 0.92 if month_offset in [5, 6] else 1.0  # Q3 budget freeze

        for bu in BUSINESS_UNITS:
            bu_weight = BU_WEIGHTS[bu]
            for service, params in SERVICES.items():
                base_cost = params["base"] * bu_weight * trend * season
                noise     = np.random.normal(1.0, params["volatility"])
                cost      = round(max(base_cost * noise, 0), 2)

                # Identify wasteful spend (rightsizing opportunity)
                waste_pct = round(np.random.uniform(0.05, 0.38), 3)
                waste_amt = round(cost * waste_pct, 2)

                records.append({
                    "month":           month_str,
                    "business_unit":   bu,
                    "aws_service":     service,
                    "total_cost_usd":  cost,
                    "waste_amount_usd": waste_amt,
                    "optimized_cost":  round(cost - waste_amt, 2),
                    "region":          np.random.choice(["us-west-2", "us-east-1", "eu-west-1"],
                                                        p=[0.55, 0.35, 0.10]),
                    "environment":     np.random.choice(["production", "staging", "dev"],
                                                        p=[0.70, 0.20, 0.10]),
                })
    return pd.DataFrame(records)


def generate_workflow_metrics():
    records = []
    start = datetime(2024, 1, 1)

    for month_offset in range(12):
        month_date = start + timedelta(days=30 * month_offset)
        month_str  = month_date.strftime("%Y-%m")

        for bu, workflows in WORKFLOW_MAP.items():
            for workflow in workflows:
                runs          = int(np.random.normal(4200, 600))
                success_rate  = round(np.random.uniform(0.91, 0.995), 4)
                avg_runtime_s = round(np.random.uniform(12, 280), 1)
                fte_saved     = round(runs * avg_runtime_s / 3600 * 0.85, 1)  # hours saved

                records.append({
                    "month":            month_str,
                    "business_unit":    bu,
                    "workflow_name":    workflow,
                    "total_runs":       runs,
                    "success_rate":     success_rate,
                    "avg_runtime_sec":  avg_runtime_s,
                    "fte_hours_saved":  fte_saved,
                    "cost_per_run_usd": round(np.random.uniform(0.04, 0.38), 4),
                })
    return pd.DataFrame(records)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    costs = generate_monthly_costs()
    costs.to_csv("data/aws_costs.csv", index=False)
    print(f"Generated aws_costs.csv — {len(costs):,} rows")

    workflows = generate_workflow_metrics()
    workflows.to_csv("data/workflow_metrics.csv", index=False)
    print(f"Generated workflow_metrics.csv — {len(workflows):,} rows")

    print("\nSample cost summary:")
    print(costs.groupby("business_unit")["total_cost_usd"].sum().sort_values(ascending=False).apply(lambda x: f"${x:,.0f}"))
