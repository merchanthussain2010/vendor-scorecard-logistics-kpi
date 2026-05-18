# Vendor Performance Scorecard & Logistics KPI Tracker
**Role:** Supply Chain Analyst | Mahindra Logistics  
**Tools:** Python (pandas, openpyxl) | Excel | SAP ERP (MM/SD/SCM modules)  
**Timeline:** Jun 2020 – Jul 2023

---

## Project Overview

Managing performance across 25+ vendors and 7 fulfillment centers manually using spreadsheets was time-consuming, inconsistent, and reactive. This project automates the end-to-end vendor performance management lifecycle — from raw SAP ERP delivery data to a weighted scorecard, tiered vendor rankings, root cause analysis, and a multi-tab Excel report ready for quarterly business reviews.

---

## Problem Statement

Mahindra Logistics' vendor reviews relied on manually compiled Excel sheets from 10+ data sources, leading to:
- Inconsistent KPI definitions across fulfillment centers
- No systematic way to compare vendors on a single composite score
- Delayed escalation of underperforming suppliers (often caught weeks late)
- No audit trail for corrective action tracking

---

## Solution

A Python-based analytics pipeline that:
1. **Ingests** delivery records from SAP MM/SD exports (or simulated data for demo)
2. **Calculates** 6 vendor KPIs per SCOR framework standards
3. **Scores** each vendor using a weighted composite model and assigns an A/B/C tier
4. **Identifies** root causes of late deliveries by vendor, FC, region, and month
5. **Quantifies** cost exposure from billing discrepancies and short-ships
6. **Exports** a ready-to-use multi-tab Excel scorecard for leadership reviews

---

## KPIs Tracked

| KPI | Weight | Definition |
|-----|--------|------------|
| OTIF % | 35% | % of deliveries that are both On-Time AND In-Full |
| Fill Rate % | 25% | Received qty ÷ Ordered qty × 100 |
| On-Time Rate % | 20% | % of deliveries arriving on or before promised date |
| Billing Accuracy % | 10% | % of invoices matching ordered amount exactly |
| Damage Rate % | 10% | % of deliveries with reported damage (inverted — lower is better) |

---

## Vendor Scoring Model

Each KPI is normalized to a 0–100 scale using min-max normalization, then combined into a **weighted composite score**. Vendors are then tiered:

| Tier | Score Range | Meaning |
|------|------------|---------|
| A – Strategic Partner | 70–100 | Exceeds standards; eligible for preferred vendor status |
| B – Meets Standards | 40–69 | Satisfactory; monitor for trends |
| C – Needs Improvement | 0–39 | At risk; corrective action plan required |

---

## Sample Output

```
─── VENDOR SCORECARD ───
Vendor                   Score   Tier                    OTIF%   OnTime%  FillRate%  AvgDelay
VND-007 | CoreLink       83.28   A – Strategic Partner   70.69   81.03    98.79      1.78
VND-006 | ReliShip       79.51   A – Strategic Partner   70.97   79.03    98.14      1.82
VND-002 | Apex Logistics  4.89   C – Needs Improvement   47.83   63.04    96.83      2.80
```

---

## Files

| File | Description |
|------|-------------|
| `vendor_scorecard.py` | Main analytics pipeline: KPI engine, scoring model, root cause analysis, cost analysis, Excel export |
| `vendor_scorecard.xlsx` | Sample output: 4-tab Excel scorecard (auto-generated on run) |

---

## Excel Output Tabs

| Tab | Contents |
|-----|----------|
| **Vendor Scorecard** | Composite score, tier, all KPIs per vendor |
| **FC Performance** | Fill rate, delay, damage rate per fulfillment center |
| **Monthly Trends** | Month-over-month KPI trend per vendor |
| **Raw Data** | Delivery-level detail for drill-down |

---

## How to Run

```bash
# Install dependencies
pip install pandas openpyxl

# Run the pipeline
python vendor_scorecard.py
```

**To use your own SAP data:** Replace the `generate_delivery_data()` call with:
```python
df = pd.read_excel("your_sap_export.xlsx")
```
Ensure your file has columns: `delivery_id`, `vendor_id`, `fulfillment_center`, `sku_id`, `promised_date`, `actual_date`, `ordered_qty`, `received_qty`, `invoice_amount_inr`, `billed_amount_inr`, `damage_reported`.

---

## Key Outcomes (at Mahindra Logistics)

- Reduced manual reporting time by automating data aggregation from 10+ sources
- Improved vendor service levels by **20%** through structured quarterly reviews backed by scorecard data
- Enabled root cause analysis on logistics delays, leading to **12% faster resolution** times
- Identified top 3 underperforming vendors (C-tier) for corrective action — 2 were replaced within 6 months
- Supported cost-per-unit benchmarking, contributing to an **11% reduction** in transportation cost per unit

---

## Skills Demonstrated

`Python` · `pandas` · `Data Analysis` · `Vendor Management` · `KPI Design` · `Supply Chain Analytics` · `SAP ERP` · `Excel Automation` · `SCOR Framework` · `Root Cause Analysis` · `Cost Analysis`
