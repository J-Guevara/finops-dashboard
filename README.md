# Cloud FinOps Governance Dashboard

**A Python-based cloud cost attribution and ROI framework for enterprise automation workloads**

Built to address a real problem: enterprise clients running automation platforms (UiPath, Power Automate, etc.) 
on AWS infrastructure couldn't answer two questions their CFOs kept asking:

1. *Which business unit is driving cloud spend?*
2. *What business value are we actually getting for that spend?*

This project maps AWS infrastructure costs to workflow-level business outcomes — turning a raw billing export 
into a QBR-ready executive view.

---

## The Problem

Enterprise TAM context: clients would receive their AWS bill, see a number like **$847,000/year**, and have 
no way to tell their VP of Finance which automation workflows were responsible or whether the spend was justified. 
Budget cuts followed. Renewals were at risk.

This framework was designed to give finance stakeholders a **cost-per-transaction** view and a clear 
**FTE savings vs. infrastructure cost** comparison — shifting the conversation from "this costs too much" 
to "this delivers 3.4x ROI."

---

## What It Does

| Module | Description |
|---|---|
| `generate_data.py` | Generates 12 months of realistic AWS cost + workflow metrics data |
| `finops_analysis.py` | Core analysis engine: spend attribution, waste detection, ROI calculation |
| `dashboard.py` | Produces 6 publication-quality charts + executive KPI summary |

### Key Outputs

- **Monthly spend trend** with MoM delta
- **Spend attribution by business unit** with waste overlay
- **AWS service cost breakdown** (donut chart)
- **ROI comparison**: infrastructure spend vs. FTE dollar value delivered
- **Rightsizing recommendations** ranked by annual savings opportunity
- **Executive KPI summary card** for QBR presentations

---

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/finops-dashboard.git
cd finops-dashboard
pip install -r requirements.txt

python generate_data.py      # creates data/aws_costs.csv and data/workflow_metrics.csv
python finops_analysis.py    # prints executive summary to terminal
python dashboard.py          # generates charts to output/charts/
```

---

## Sample Output

### Executive Summary (terminal)
```
Total Infra Spend Usd               $   847,320
Recoverable Waste Usd               $   214,680
Waste Percentage                          25.3%
Total Workflow Runs                    604,800
Fte Hours Saved                        312,440
Fte Dollar Value Usd                $20,308,600
Net Roi Usd                         $19,461,280
Overall Roi Multiple                       23.96
Avg Workflow Success Pct                   95.8%
Cost Per Transaction Usd                  0.0014
```

---

## Methodology

### Spend Attribution
Costs are allocated to business units using a weight-based model derived from resource tagging 
(simulated here; production implementation uses AWS Cost Allocation Tags).

### Waste Identification
Waste percentage is calculated per service per environment using a rightsizing heuristic that flags 
resources operating below utilization thresholds — consistent with AWS Trusted Advisor recommendations.

### ROI Calculation
FTE value delivered is calculated as:
```
FTE Hours Saved = (Total Runs × Avg Runtime) / 3600 × 0.85
FTE Dollar Value = FTE Hours Saved × $65/hr (blended rate)
Net ROI = FTE Dollar Value − Infrastructure Spend
```

### Interview Discussion Points
- Why $65/hr blended rate? Conservative estimate covering fully-loaded cost (salary + benefits + overhead) 
  for the mix of knowledge workers whose work is being automated.
- Why 0.85 efficiency factor? Accounts for bot exceptions, reruns, and human oversight time — 
  avoids overstating savings.
- Production extension: plug in actual AWS Cost Explorer API exports + UiPath Insights API data 
  for live numbers.

---

## Tech Stack

- **Python 3.10+**
- pandas, numpy — data manipulation and analysis
- matplotlib, seaborn — visualization
- AWS Cost Explorer (production data source)
- UiPath Insights API (production workflow metrics source)

---

## Real-World Application

This framework was developed based on patterns observed across enterprise automation accounts where 
cloud infrastructure costs were a recurring renewal risk factor. The ROI attribution model was 
adopted as a standard QBR template, contributing to improved gross retention across a TAM portfolio.

---

## Author

**Josue Guevara**  
Technical Account Manager II| Cloud & AI Automation  
[LinkedIn](https://www.linkedin.com/in/jguevara2/) | San Diego, CA
