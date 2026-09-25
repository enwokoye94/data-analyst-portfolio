#!/usr/bin/env python3
"""
RFM segment analysis: runs rfm_analysis.sql, summarizes segments in pandas,
saves charts to charts/, and writes results.md.

Deterministic: the SQL uses a fixed "as of" date; no randomness here.
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "customers.db"
SQL = ROOT / "rfm_analysis.sql"
CHARTS = ROOT / "charts"

SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Potential Loyalists", "New Customers",
    "Need Attention", "At Risk", "Can't Lose Them", "Hibernating", "Lost",
]
COLORS = {
    "Champions": "#1b7f5a", "Loyal Customers": "#2ca868",
    "Potential Loyalists": "#7ccba1", "New Customers": "#a6d854",
    "Need Attention": "#e6b800", "At Risk": "#e07b39",
    "Can't Lose Them": "#c0392b", "Hibernating": "#7f8c8d", "Lost": "#4a4a4a",
}

plt.rcParams.update({"figure.dpi": 130, "font.size": 10})


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    script = SQL.read_text()
    con = sqlite3.connect(DB)
    con.executescript(script)  # (re)builds the customer_rfm view

    rfm = pd.read_sql("SELECT * FROM customer_rfm", con)
    assert rfm["segment"].notna().all(), "unsegmented customers!"
    con.close()

    summary = (
        rfm.groupby("segment", observed=True)
        .agg(customers=("customer_id", "count"),
             total_revenue=("monetary", "sum"),
             avg_monetary=("monetary", "mean"),
             avg_recency_days=("recency_days", "mean"),
             avg_frequency=("frequency", "mean"))
        .reset_index()
    )
    summary["pct_of_customers"] = (100 * summary["customers"] / summary["customers"].sum()).round(1)
    summary["pct_of_revenue"] = (100 * summary["total_revenue"] / summary["total_revenue"].sum()).round(1)
    summary["avg_monetary"] = summary["avg_monetary"].round(0)
    summary["avg_recency_days"] = summary["avg_recency_days"].round(0)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)
    summary["order"] = summary["segment"].map({s: i for i, s in enumerate(SEGMENT_ORDER)})
    summary = summary.sort_values("total_revenue", ascending=False).reset_index(drop=True)

    n_customers = len(rfm)
    total_rev = rfm["monetary"].sum()
    print(f"{n_customers} customers, ${total_rev:,.0f} total revenue, "
          f"{summary['segment'].nunique()} segments")

    # --- Chart 1: segment sizes -------------------------------------------------
    s1 = summary.sort_values("customers", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(s1["segment"], s1["customers"],
            color=[COLORS[s] for s in s1["segment"]])
    for y, v in zip(s1["segment"], s1["customers"]):
        ax.text(v + 8, y, f"{v:,}", va="center", fontsize=9)
    ax.set_xlabel("Customers")
    ax.set_title("Customers per RFM Segment (n=2,000)")
    fig.tight_layout()
    fig.savefig(CHARTS / "segment_sizes.png")
    plt.close(fig)

    # --- Chart 2: average monetary by segment ------------------------------------
    s2 = summary.sort_values("avg_monetary", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(s2["segment"], s2["avg_monetary"],
            color=[COLORS[s] for s in s2["segment"]])
    for y, v in zip(s2["segment"], s2["avg_monetary"]):
        ax.text(v + 300, y, f"${v:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Average lifetime revenue per customer ($)")
    ax.set_title("Average Customer Value by Segment")
    fig.tight_layout()
    fig.savefig(CHARTS / "avg_monetary_by_segment.png")
    plt.close(fig)

    # --- Chart 3: recency distribution -------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(rfm["recency_days"], bins=50, color="#2c7fb8", edgecolor="white")
    ax.axvline(rfm["recency_days"].median(), color="#c0392b", linestyle="--",
               label=f"Median: {rfm['recency_days'].median():.0f} days")
    ax.set_xlabel("Days since last purchase (as of 2026-09-30)")
    ax.set_ylabel("Customers")
    ax.set_title("Recency Distribution — a long tail of disengaged customers")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "recency_distribution.png")
    plt.close(fig)

    # --- Chart 4: revenue share donut ----------------------------------------------
    s4 = summary.sort_values("total_revenue", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, _ = ax.pie(
        s4["total_revenue"],
        colors=[COLORS[s] for s in s4["segment"]],
        startangle=90,
        wedgeprops={"width": 0.4, "edgecolor": "white"})
    ax.legend(wedges,
              [f"{s} — {p:.1f}%" for s, p in zip(s4["segment"], s4["pct_of_revenue"])],
              loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9,
              title="Segment — revenue share")
    ax.set_title("Revenue Concentration by Segment")
    fig.tight_layout()
    fig.savefig(CHARTS / "revenue_share.png", bbox_inches="tight")
    plt.close(fig)

    # --- results.md ----------------------------------------------------------------
    lines = [
        "# RFM Segmentation — Results",
        "",
        f"**As of:** 2026-09-30 · **Customers:** {n_customers:,} · "
        f"**Total revenue:** ${total_rev:,.0f}",
        "",
        "| Segment | Customers | % of Customers | Revenue | % of Revenue | "
        "Avg $/Customer | Avg Recency (days) | Avg Txns |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['segment']} | {r['customers']:,} | {r['pct_of_customers']}% | "
            f"${r['total_revenue']:,.0f} | {r['pct_of_revenue']}% | "
            f"${r['avg_monetary']:,.0f} | {r['avg_recency_days']:.0f} | {r['avg_frequency']:.1f} |"
        )
    top3 = summary.head(3)
    atrisk = summary[summary["segment"].isin(["At Risk", "Can't Lose Them", "Hibernating"])]
    lines += [
        "",
        "## Headlines",
        "",
        f"- Top 3 segments ({', '.join(top3['segment'])}) = "
        f"**{top3['customers'].sum():,} customers ({100*top3['customers'].sum()/n_customers:.1f}%)** "
        f"driving **${top3['total_revenue'].sum():,.0f} "
        f"({top3['pct_of_revenue'].sum():.1f}% of revenue)**.",
        f"- **${atrisk['total_revenue'].sum():,.0f}** of historical revenue sits in "
        f"'{', '.join(atrisk['segment'])}' ({atrisk['customers'].sum():,} customers) — "
        "the win-back priority list.",
        f"- Median recency is **{rfm['recency_days'].median():.0f} days**; "
        f"{(rfm['recency_days'] > 365).sum():,} customers ({100*(rfm['recency_days'] > 365).mean():.1f}%) "
        "haven't purchased in over a year.",
    ]
    (ROOT / "results.md").write_text("\n".join(lines) + "\n")
    print("wrote results.md and 4 charts")


if __name__ == "__main__":
    main()
