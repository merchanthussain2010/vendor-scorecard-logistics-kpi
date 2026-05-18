"""
============================================================
Project: Vendor Performance Scorecard & Logistics KPI Tracker
Author:  Hussain Merchant
Role:    Supply Chain Analyst | Mahindra Logistics
Tools:   Python (pandas, openpyxl) | Excel | SAP ERP data exports
Purpose: Automate vendor KPI calculation, scorecard generation,
         and logistics performance reporting across 25+ suppliers
         and 7 fulfillment centers
============================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# SECTION 1: SAMPLE DATA GENERATION
# Represents SAP ERP exports / WMS data from Mahindra Logistics
# Replace with actual file loads: pd.read_excel("sap_export.xlsx")
# ─────────────────────────────────────────────────────────────

np.random.seed(42)
N_DELIVERIES = 500

VENDORS = [
    "VND-001 | BlueStar Freight",
    "VND-002 | Apex Logistics",
    "VND-003 | Primus Carriers",
    "VND-004 | Horizon Transport",
    "VND-005 | SwiftMove Pvt Ltd",
    "VND-006 | ReliShip India",
    "VND-007 | CoreLink Supply",
    "VND-008 | FastRoute Express",
]

FULFILLMENT_CENTERS = ["FC-Pune", "FC-Mumbai", "FC-Nagpur", "FC-Delhi", "FC-Chennai", "FC-Hyderabad", "FC-Bangalore"]
SKUS = [f"SKU-{str(i).zfill(4)}" for i in range(1, 51)]

def generate_delivery_data(n=N_DELIVERIES):
    """Simulate SAP MM / SD module delivery records"""
    base_date = datetime(2022, 4, 1)
    data = {
        "delivery_id":        [f"DEL-{str(i).zfill(5)}" for i in range(1, n+1)],
        "vendor_id":          np.random.choice(VENDORS, n),
        "fulfillment_center": np.random.choice(FULFILLMENT_CENTERS, n),
        "sku_id":             np.random.choice(SKUS, n),
        "promised_date":      [base_date + timedelta(days=int(d)) for d in np.random.randint(0, 450, n)],
        "actual_date":        None,   # filled below
        "ordered_qty":        np.random.randint(50, 500, n),
        "received_qty":       None,   # filled below
        "invoice_amount_inr": np.random.randint(10000, 500000, n),
        "billed_amount_inr":  None,   # filled below
        "damage_reported":    np.random.choice([0, 1], n, p=[0.92, 0.08]),
        "region":             np.random.choice(["West", "North", "South", "East"], n),
    }

    df = pd.DataFrame(data)

    # Simulate delays: most on-time, some late
    delay_days = np.where(
        np.random.random(n) < 0.78,     # 78% on-time
        np.random.randint(-2, 1, n),    # early or on-time
        np.random.randint(1, 15, n)     # late
    )
    df["actual_date"] = df["promised_date"] + pd.to_timedelta(delay_days, unit="d")
    df["delay_days"]  = delay_days.clip(min=0)

    # Received qty: most 100%, some short-ships
    fill_rate = np.where(np.random.random(n) < 0.85, 1.0, np.random.uniform(0.7, 0.99, n))
    df["received_qty"] = (df["ordered_qty"] * fill_rate).astype(int)

    # Billing accuracy: some invoices have errors
    billing_error = np.where(np.random.random(n) < 0.90, 1.0, np.random.uniform(0.95, 1.05, n))
    df["billed_amount_inr"] = (df["invoice_amount_inr"] * billing_error).astype(int)

    df["on_time_flag"]       = (df["delay_days"] == 0).astype(int)
    df["fill_rate_pct"]      = (df["received_qty"] / df["ordered_qty"] * 100).round(2)
    df["billing_match_flag"] = (df["billed_amount_inr"] == df["invoice_amount_inr"]).astype(int)
    df["month"]              = df["promised_date"].dt.to_period("M")

    return df


# ─────────────────────────────────────────────────────────────
# SECTION 2: KPI CALCULATION ENGINE
# ─────────────────────────────────────────────────────────────

def calculate_vendor_kpis(df):
    """
    Compute core vendor KPIs aligned with SCOR framework:
    - OTIF (On-Time In-Full)
    - Fill Rate %
    - Average Delay (days)
    - Billing Accuracy %
    - Damage Rate %
    - Total Spend (INR)
    """
    kpis = df.groupby("vendor_id").agg(
        total_deliveries    = ("delivery_id",        "count"),
        on_time_count       = ("on_time_flag",        "sum"),
        avg_delay_days      = ("delay_days",          "mean"),
        total_ordered_qty   = ("ordered_qty",         "sum"),
        total_received_qty  = ("received_qty",        "sum"),
        billing_match_count = ("billing_match_flag",  "sum"),
        damage_count        = ("damage_reported",     "sum"),
        total_spend_inr     = ("invoice_amount_inr",  "sum"),
    ).reset_index()

    kpis["on_time_rate_pct"]      = (kpis["on_time_count"]       / kpis["total_deliveries"]  * 100).round(2)
    kpis["fill_rate_pct"]         = (kpis["total_received_qty"]   / kpis["total_ordered_qty"] * 100).round(2)
    kpis["billing_accuracy_pct"]  = (kpis["billing_match_count"]  / kpis["total_deliveries"]  * 100).round(2)
    kpis["damage_rate_pct"]       = (kpis["damage_count"]         / kpis["total_deliveries"]  * 100).round(2)
    kpis["avg_delay_days"]        = kpis["avg_delay_days"].round(2)

    # OTIF = On-Time AND In-Full (conservative, most important metric)
    otif = df.groupby("vendor_id").apply(
        lambda x: ((x["on_time_flag"] == 1) & (x["received_qty"] == x["ordered_qty"])).mean() * 100
    ).round(2).reset_index(name="otif_pct")
    kpis = kpis.merge(otif, on="vendor_id")

    return kpis


def calculate_fc_kpis(df):
    """Fulfillment Center level performance metrics"""
    fc_kpis = df.groupby("fulfillment_center").agg(
        total_deliveries   = ("delivery_id",   "count"),
        avg_fill_rate      = ("fill_rate_pct", "mean"),
        avg_delay_days     = ("delay_days",    "mean"),
        damage_count       = ("damage_reported","sum"),
        total_spend_inr    = ("invoice_amount_inr", "sum"),
        unique_vendors     = ("vendor_id",     "nunique"),
        unique_skus        = ("sku_id",        "nunique"),
    ).reset_index()

    fc_kpis["avg_fill_rate"]  = fc_kpis["avg_fill_rate"].round(2)
    fc_kpis["avg_delay_days"] = fc_kpis["avg_delay_days"].round(2)
    fc_kpis["damage_rate_pct"] = (fc_kpis["damage_count"] / fc_kpis["total_deliveries"] * 100).round(2)
    return fc_kpis


def calculate_monthly_trends(df):
    """Month-over-month KPI trend for executive reporting"""
    monthly = df.groupby(["month", "vendor_id"]).agg(
        deliveries       = ("delivery_id",   "count"),
        on_time_rate     = ("on_time_flag",   "mean"),
        fill_rate        = ("fill_rate_pct",  "mean"),
        avg_delay        = ("delay_days",     "mean"),
        spend_inr        = ("invoice_amount_inr", "sum"),
    ).reset_index()

    monthly["on_time_rate"] = (monthly["on_time_rate"] * 100).round(2)
    monthly["fill_rate"]    = monthly["fill_rate"].round(2)
    monthly["avg_delay"]    = monthly["avg_delay"].round(2)
    monthly["month"]        = monthly["month"].astype(str)
    return monthly


# ─────────────────────────────────────────────────────────────
# SECTION 3: VENDOR SCORING MODEL
# Weighted composite score → tiering (A/B/C)
# ─────────────────────────────────────────────────────────────

WEIGHTS = {
    "otif_pct":            0.35,   # most important
    "fill_rate_pct":       0.25,
    "on_time_rate_pct":    0.20,
    "billing_accuracy_pct":0.10,
    "damage_rate_pct":     0.10,   # inverted below
}

def score_vendors(kpis):
    """
    Normalize each KPI to 0–100 and compute a weighted composite score.
    damage_rate_pct is inverted (lower = better).
    """
    df = kpis.copy()

    # Normalize positive metrics (higher = better)
    for col in ["otif_pct", "fill_rate_pct", "on_time_rate_pct", "billing_accuracy_pct"]:
        min_v, max_v = df[col].min(), df[col].max()
        df[f"{col}_norm"] = (df[col] - min_v) / (max_v - min_v + 1e-9) * 100

    # Normalize inverted metric (lower damage = better score)
    min_v, max_v = df["damage_rate_pct"].min(), df["damage_rate_pct"].max()
    df["damage_rate_pct_norm"] = (1 - (df["damage_rate_pct"] - min_v) / (max_v - min_v + 1e-9)) * 100

    df["composite_score"] = (
        df["otif_pct_norm"]             * WEIGHTS["otif_pct"]            +
        df["fill_rate_pct_norm"]        * WEIGHTS["fill_rate_pct"]       +
        df["on_time_rate_pct_norm"]     * WEIGHTS["on_time_rate_pct"]    +
        df["billing_accuracy_pct_norm"] * WEIGHTS["billing_accuracy_pct"]+
        df["damage_rate_pct_norm"]      * WEIGHTS["damage_rate_pct"]
    ).round(2)

    # Tier assignment
    df["tier"] = pd.cut(
        df["composite_score"],
        bins=[0, 40, 70, 100],
        labels=["C – Needs Improvement", "B – Meets Standards", "A – Strategic Partner"],
        include_lowest=True
    )

    return df.sort_values("composite_score", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# SECTION 4: ROOT CAUSE ANALYSIS — DELAY DEEP DIVE
# ─────────────────────────────────────────────────────────────

def delay_root_cause_analysis(df):
    """
    Identify top contributing factors to late deliveries:
    by vendor, fulfillment center, SKU, region, and month
    """
    late = df[df["delay_days"] > 0].copy()

    print("\n" + "="*60)
    print("ROOT CAUSE ANALYSIS: LATE DELIVERIES")
    print("="*60)

    print(f"\nTotal deliveries: {len(df)}")
    print(f"Late deliveries:  {len(late)} ({len(late)/len(df)*100:.1f}%)")
    print(f"Avg delay (late only): {late['delay_days'].mean():.1f} days")

    print("\n--- Top 5 Vendors by Late Delivery Count ---")
    vendor_late = late.groupby("vendor_id")["delivery_id"].count().sort_values(ascending=False).head(5)
    print(vendor_late.to_string())

    print("\n--- Late Deliveries by Fulfillment Center ---")
    fc_late = late.groupby("fulfillment_center")["delivery_id"].count().sort_values(ascending=False)
    print(fc_late.to_string())

    print("\n--- Average Delay by Region (days) ---")
    region_delay = late.groupby("region")["delay_days"].mean().sort_values(ascending=False).round(2)
    print(region_delay.to_string())

    print("\n--- Monthly Late Delivery Trend ---")
    monthly_late = late.groupby("month")["delivery_id"].count().reset_index()
    monthly_late.columns = ["month", "late_count"]
    monthly_late["month"] = monthly_late["month"].astype(str)
    print(monthly_late.tail(12).to_string(index=False))

    return late


# ─────────────────────────────────────────────────────────────
# SECTION 5: COST REDUCTION ANALYSIS
# ─────────────────────────────────────────────────────────────

def cost_analysis(df):
    """
    Identify cost inefficiencies:
    - Short-ship cost exposure (ordered not received)
    - Billing discrepancies
    - Vendor cost per unit comparison
    """
    df = df.copy()
    df["undelivered_qty"] = df["ordered_qty"] - df["received_qty"]
    df["billing_discrepancy_inr"] = abs(df["billed_amount_inr"] - df["invoice_amount_inr"])
    df["cost_per_unit"] = df["invoice_amount_inr"] / df["ordered_qty"].replace(0, np.nan)

    print("\n" + "="*60)
    print("COST ANALYSIS SUMMARY")
    print("="*60)
    print(f"\nTotal spend (INR):              ₹{df['invoice_amount_inr'].sum():,.0f}")
    print(f"Total billing discrepancies:    ₹{df['billing_discrepancy_inr'].sum():,.0f}")
    print(f"Pct of spend with errors:       {df[df['billing_discrepancy_inr']>0]['invoice_amount_inr'].sum()/df['invoice_amount_inr'].sum()*100:.1f}%")

    print("\n--- Cost Per Unit by Vendor (INR) ---")
    cpu = df.groupby("vendor_id")["cost_per_unit"].mean().sort_values().round(2)
    print(cpu.to_string())

    print("\n--- Top Fulfillment Centers by Short-Ship Qty ---")
    shortship = df.groupby("fulfillment_center")["undelivered_qty"].sum().sort_values(ascending=False)
    print(shortship.to_string())

    return df


# ─────────────────────────────────────────────────────────────
# SECTION 6: EXPORT SCORECARD TO EXCEL
# ─────────────────────────────────────────────────────────────

def export_scorecard_to_excel(vendor_scores, fc_kpis, monthly_trends, raw_df, output_path="vendor_scorecard.xlsx"):
    """
    Export a multi-tab Excel scorecard — mirrors the manual reporting
    process automated for Mahindra Logistics' 25+ vendor reviews
    """
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Tab 1: Vendor Scorecard
            cols = [
                "vendor_id", "composite_score", "tier",
                "otif_pct", "on_time_rate_pct", "fill_rate_pct",
                "billing_accuracy_pct", "damage_rate_pct",
                "avg_delay_days", "total_deliveries", "total_spend_inr"
            ]
            vendor_scores[cols].to_excel(writer, sheet_name="Vendor Scorecard", index=False)

            # Tab 2: Fulfillment Center KPIs
            fc_kpis.to_excel(writer, sheet_name="FC Performance", index=False)

            # Tab 3: Monthly Trends
            monthly_trends.to_excel(writer, sheet_name="Monthly Trends", index=False)

            # Tab 4: Raw Delivery Data
            export_cols = [
                "delivery_id", "vendor_id", "fulfillment_center", "sku_id",
                "promised_date", "actual_date", "delay_days", "on_time_flag",
                "ordered_qty", "received_qty", "fill_rate_pct",
                "invoice_amount_inr", "billed_amount_inr", "damage_reported"
            ]
            raw_df[export_cols].to_excel(writer, sheet_name="Raw Data", index=False)

        print(f"\n✅ Scorecard exported to: {output_path}")
    except Exception as e:
        print(f"\n⚠️  Excel export skipped ({e}). CSV export:")
        vendor_scores[cols].to_csv("vendor_scorecard.csv", index=False)
        print("   vendor_scorecard.csv created.")


# ─────────────────────────────────────────────────────────────
# SECTION 7: MAIN EXECUTION
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("VENDOR PERFORMANCE SCORECARD & LOGISTICS KPI TRACKER")
    print("Mahindra Logistics | Supply Chain Analytics")
    print("=" * 60)

    # 1. Load / generate data
    print("\n[1/5] Loading delivery data...")
    df = generate_delivery_data(N_DELIVERIES)
    print(f"     {len(df)} delivery records loaded across {df['vendor_id'].nunique()} vendors")

    # 2. Calculate KPIs
    print("\n[2/5] Calculating vendor KPIs...")
    vendor_kpis  = calculate_vendor_kpis(df)
    fc_kpis      = calculate_fc_kpis(df)
    monthly_data = calculate_monthly_trends(df)

    # 3. Score and tier vendors
    print("\n[3/5] Scoring and tiering vendors...")
    vendor_scores = score_vendors(vendor_kpis)

    print("\n─── VENDOR SCORECARD ───")
    scorecard_display = vendor_scores[[
        "vendor_id", "composite_score", "tier",
        "otif_pct", "on_time_rate_pct", "fill_rate_pct", "avg_delay_days"
    ]].copy()
    scorecard_display.columns = ["Vendor", "Score", "Tier", "OTIF%", "OnTime%", "FillRate%", "AvgDelay(days)"]
    print(scorecard_display.to_string(index=False))

    print("\n─── FULFILLMENT CENTER KPIs ───")
    print(fc_kpis[[
        "fulfillment_center", "total_deliveries", "avg_fill_rate",
        "avg_delay_days", "damage_rate_pct", "unique_vendors"
    ]].to_string(index=False))

    # 4. Root cause & cost analysis
    print("\n[4/5] Running root cause and cost analyses...")
    delay_root_cause_analysis(df)
    df_cost = cost_analysis(df)

    # 5. Export scorecard
    print("\n[5/5] Exporting scorecard to Excel...")
    export_scorecard_to_excel(vendor_scores, fc_kpis, monthly_data, df)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"  Vendors analyzed:          {len(vendor_scores)}")
    print(f"  Fulfillment centers:       {len(fc_kpis)}")
    print(f"  Total deliveries reviewed: {len(df)}")
    print(f"  A-tier vendors:            {(vendor_scores['tier'] == 'A – Strategic Partner').sum()}")
    print(f"  C-tier vendors (at risk):  {(vendor_scores['tier'] == 'C – Needs Improvement').sum()}")
    print("="*60)
