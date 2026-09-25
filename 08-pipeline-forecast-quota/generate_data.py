"""
generate_data.py — Synthetic sales pipeline history generator.

Creates 24 months (Jan 2024 - Dec 2025) of monthly pipeline data per segment.
Everything is synthetic and reproducible (fixed random seed).

Signals baked in:
  - Seasonality: Q4 budget-flush spike (Nov peak), Q1 dip, summer softness
  - Trend: steady YoY growth (SMB fastest, Enterprise slowest)
  - Noise: moderate random variation around the signal
  - Quotas: set each year to grow ~18% YoY, landing slightly above expected
    won bookings, so attainment hovers around 95-105% with real risk pockets.

Columns:
  month, segment, pipeline_created, pipeline_won, quota,
  avg_sales_cycle_days, win_rate
"""
import numpy as np
import pandas as pd
from pathlib import Path

RNG_SEED = 42
OUT = Path(__file__).resolve().parent / "data" / "pipeline_history.csv"

SEGMENTS = {
    # base monthly pipeline created, annual growth, win rate, cycle days
    "SMB":        {"base": 520_000, "annual_growth": 0.22, "win_rate": 0.34, "cycle": 24},
    "Mid-Market": {"base": 940_000, "annual_growth": 0.16, "win_rate": 0.28, "cycle": 52},
    "Enterprise": {"base": 1_350_000, "annual_growth": 0.10, "win_rate": 0.23, "cycle": 96},
}

# Multiplicative seasonal index by calendar month (1-12). Q4 spike, Q1 dip.
SEASONALITY = {
    1: 0.78, 2: 0.82, 3: 0.98, 4: 0.95, 5: 0.96, 6: 0.99,
    7: 0.90, 8: 0.88, 9: 1.02, 10: 1.12, 11: 1.28, 12: 1.32,
}
# Enterprise seasonality is more back-loaded (end-of-year big deals)
ENTERPRISE_SEASONAL_BOOST = {10: 1.04, 11: 1.08, 12: 1.10}

rng = np.random.default_rng(RNG_SEED)
months = pd.date_range("2024-01-01", periods=24, freq="MS")

rows = []
for seg, cfg in SEGMENTS.items():
    for i, month in enumerate(months):
        t_years = i / 12.0
        seasonal = SEASONALITY[month.month]
        if seg == "Enterprise":
            seasonal *= ENTERPRISE_SEASONAL_BOOST.get(month.month, 1.0)

        trend = (1 + cfg["annual_growth"]) ** t_years
        signal = cfg["base"] * seasonal * trend
        pipeline_created = int(round(signal * rng.normal(1.0, 0.07)))

        # Win rate wiggles a little; Q4 tends to convert slightly better.
        q4_lift = 1.04 if month.month in (10, 11, 12) else 1.0
        win_rate = float(np.clip(
            cfg["win_rate"] * q4_lift * rng.normal(1.0, 0.05), 0.05, 0.90
        ))
        pipeline_won = int(round(pipeline_created * win_rate))

        # Quotas are set on *bookings* (pipeline_won scale), not pipeline
        # created: expected won = base x win_rate, growing ~18% YoY with a Q4
        # ratchet. SMB (22% growth) outruns quota; Enterprise (10% growth +
        # an aggressive H2-2025 hike) falls behind — the "risk" story.
        quota = int(round(cfg["base"] * cfg["win_rate"] * (1.18 ** t_years)
                          * (1.25 if month.month in (10, 11, 12) else 1.0) * 1.03))
        if seg == "Enterprise" and month >= pd.Timestamp("2025-07-01"):
            quota = int(round(quota * 1.12))  # aggressive H2 quota hike

        avg_cycle = int(round(cfg["cycle"] * rng.normal(1.0, 0.08)))

        rows.append({
            "month": month.strftime("%Y-%m"),
            "segment": seg,
            "pipeline_created": pipeline_created,
            "pipeline_won": pipeline_won,
            "quota": quota,
            "avg_sales_cycle_days": avg_cycle,
            "win_rate": round(win_rate, 4),
        })

df = pd.DataFrame(rows, columns=[
    "month", "segment", "pipeline_created", "pipeline_won",
    "quota", "avg_sales_cycle_days", "win_rate",
])
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {OUT} — {len(df)} rows, seed={RNG_SEED}")
print(df.groupby("segment")["pipeline_created"].sum().to_string())
