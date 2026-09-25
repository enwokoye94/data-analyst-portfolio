# Sales Pipeline Forecast & Quota Attainment

**Can we hit quota next half — and where exactly is the risk?**

A sales-operations forecasting project: 24 months of synthetic pipeline history
across three segments, a transparent seasonal-trend forecast for the next two
quarters, a holdout backtest proving the model earns trust, and a quota-attainment
risk flag plus the pipeline coverage math ops leaders actually use.

## Business problem

Leadership needs to know *before* H1 2026 starts whether each segment's quota is
reachable, how much pipeline must be created to cover it, and where to intervene
early. A forecast nobody can explain is a forecast nobody will act on — so the
method here is deliberately simple and auditable.

## Data (all synthetic, reproducible)

`generate_data.py` (seed = 42) builds `data/pipeline_history.csv`: 24 months
(Jan 2024 – Dec 2025) × 3 segments (SMB, Mid-Market, Enterprise), with:

- **Seasonality** — Q4 budget-flush spike (Dec index 1.32), Q1 dip (Jan 0.78)
- **Trend** — steady YoY growth (SMB 22%, Mid-Market 16%, Enterprise 10%)
- **Noise** — ±7% on pipeline, ±5% on win rate
- **Quotas** — ~18% YoY growth with a Q4 ratchet; Enterprise got an extra
  12% quota hike in H2 2025, which is exactly what creates the risk story

Columns: `month, segment, pipeline_created, pipeline_won, quota,
avg_sales_cycle_days, win_rate`

## Method — and why it's explainable

No black boxes. For each segment:

1. **Seasonal index** per calendar month = mean(actual ÷ centered 12-month
   moving average) — i.e. "Novembers run 28% above trend," printed in the data.
2. **Trend** = ordinary least-squares line on the deseasonalized series.
3. **Forecast** = `trend(t+h) × seasonal_index[month]` — you can hand-check any
   number with a calculator.
4. **Backtest** — train on the first 18 months, forecast the last 2 quarters,
   compare to actuals (MAPE). If the method can't predict the recent past,
   the future forecast isn't trusted.
5. **Attainment %** = forecast bookings ÷ forecast quota. **Pipeline coverage
   needed** = quota ÷ trailing-6-month win rate.

## Key findings (from the actual run)

**Backtest accuracy** — the method predicts the held-out 2 quarters with:

| Segment | MAPE |
|---|---|
| Enterprise | 12.4% |
| Mid-Market | 8.9% |
| SMB | 7.0% |
| **Average** | **9.4%** |

Enterprise is hardest to predict (lumpier big deals); SMB is the most stable.

**H1 2026 forecast attainment:**

| Segment | Forecast bookings | Forecast quota | Attainment | Status |
|---|---|---|---|---|
| Enterprise | $2.22M | $2.96M | **74.9%** | 🔴 AT RISK |
| Mid-Market | $2.11M | $2.32M | **91.1%** | 🟡 WATCH |
| SMB | $1.45M | $1.56M | **93.1%** | 🟡 WATCH |

**Enterprise is the problem.** It's forecast to miss quota by **~$742K**
(25 points), and this isn't a blip — actual attainment fell from 91.7% in
Q2 2025 to 70.7% in Q3 2025 right after the H2 quota hike. The forecast simply
extends a trend that's already visible.

**Pipeline coverage gap** (quota ÷ win rate vs. forecast pipeline):

| Segment | Win rate | Pipeline needed | Pipeline forecast | Gap |
|---|---|---|---|---|
| Enterprise | 22.9% | $12.9M | $9.5M | **−$3.4M** |
| Mid-Market | 28.4% | $8.2M | $7.5M | −$0.7M |
| SMB | 33.9% | $4.6M | $4.2M | −$0.4M |

See `results.md` for the full month-by-month forecast table and `charts/` for
actuals-vs-forecast (with backtest shading), attainment bars, and coverage gap.

## Recommended ops actions

1. **Enterprise quota relief or re-plan.** A $3.4M pipeline gap at a 22.9%
   win rate can't be closed by "selling harder." Options: trim the H1 quota
   ~15%, shift ~$2M of quota to SMB/Mid-Market (both near 93%+ on current
   trajectory), or fund targeted pipeline-gen (ABM, partner sourcing).
2. **Put Mid-Market and SMB on a monthly watch.** Both forecast 91–93% —
   inside the backtest error band (7–9% MAPE), so they're coin flips. Track
   monthly coverage ratio; intervene if it drops below 3x.
3. **Attack Enterprise win rate.** Coverage needed = quota ÷ win rate, so
   lifting Enterprise win rate from 22.9% → 27% cuts required pipeline from
   $12.9M to ~$11.0M. Deal reviews and loss analysis are the lever.
4. **Re-forecast monthly.** The script reruns in seconds — bake it into the
   monthly ops cadence so the forecast absorbs new actuals.

## Skills demonstrated

- Time-series forecasting with explainable seasonal-trend decomposition
  (moving-average seasonal indices + OLS trend) — sklearn, pandas, numpy
- Backtesting discipline: holdout validation with MAPE before trusting a forecast
- Sales-ops metrics: quota attainment, pipeline coverage (quota ÷ win rate),
  win-rate trending, risk flagging
- Reproducible synthetic data design with realistic seasonality/trend/noise
- Executive-ready charts (matplotlib) and tabular reporting

## How to run

```bash
python generate_data.py   # builds data/pipeline_history.csv (seed 42)
python forecast.py        # prints backtest + forecast, writes charts/ and results.md
```

Environment: Python 3.12, pandas 3, scikit-learn 1.9, matplotlib 3.11.
