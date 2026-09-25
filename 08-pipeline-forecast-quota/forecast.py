"""
forecast.py — Explainable 2-quarter pipeline & quota-attainment forecast.

Method (deliberately transparent, no black boxes):
  1. For each segment, decompose the monthly series into
     SEASONALITY x TREND using a centered 12-month moving average.
     - seasonal_index[calendar_month] = mean(actual / moving_avg)
     - deseasonalized = actual / seasonal_index
     - trend(t) = LinearRegression(time_index) fit on deseasonalized
  2. Forecast h months out:  trend(t+h) * seasonal_index[month(t+h)].
     Applied to both `pipeline_won` (bookings) and `quota`
     (quotas are seasonal too — Q4 budget ratchets).
  3. Backtest: train on months 1-18, forecast months 19-24 (last 2 quarters),
     report MAPE per segment on `pipeline_won`.
  4. Forecast Jan-Jun 2026 (2 quarters). Attainment % = forecast_won / forecast_quota.
     Pipeline coverage needed = quota / win_rate; flag segments < 95% attainment.

Outputs:
  charts/forecast_by_segment.png   — actuals vs forecast, holdout shaded
  charts/attainment_by_segment.png — H1-2026 forecast attainment per segment
  charts/coverage_gap.png          — required vs forecasted pipeline coverage
  results.md                       — forecast table per segment x month
Prints: backtest MAPE, attainment %, at-risk flags, coverage math.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "pipeline_history.csv"
CHARTS = ROOT / "charts"
RESULTS = ROOT / "results.md"

TRAIN_MONTHS = 18          # Jan 2024 - Jun 2025
HOLDOUT_MONTHS = 6        # Jul 2025 - Dec 2025 (last 2 quarters)
FORECAST_MONTHS = 6       # Jan 2026 - Jun 2026
TARGET = "pipeline_won"

# ---------------------------------------------------------------- helpers
def seasonal_trend_fit(series: pd.Series):
    """Return (seasonal_index dict, trend model) for a monthly series."""
    vals = series.to_numpy(dtype=float)
    t = np.arange(len(vals)).reshape(-1, 1)
    # centered 12-month moving average as the trend-cycle estimate
    ma = pd.Series(vals).rolling(12, center=True).mean().to_numpy()
    seasonal = {}
    for m in range(1, 13):
        mask = (series.index.month == m) & ~np.isnan(ma) & (ma != 0)
        seasonal[m] = float(np.mean(vals[mask] / ma[mask])) if mask.sum() else 1.0
    # normalize so seasonal indices average ~1
    mean_s = float(np.mean(list(seasonal.values())))
    seasonal = {m: v / mean_s for m, v in seasonal.items()}
    deseason = vals / np.array([seasonal[m] for m in series.index.month])
    model = LinearRegression().fit(t, deseason)
    return seasonal, model


def forecast_series(train: pd.Series, seasonal, model, future_months: pd.DatetimeIndex):
    """trend(t+h) * seasonal_index[month(t+h)] for each future month."""
    n_train = len(train)
    out = []
    for h, m in enumerate(future_months):
        t_h = np.array([[n_train + h]])
        out.append(float(model.predict(t_h)[0] * seasonal[m.month]))
    return pd.Series(out, index=future_months)


def mape(actual, forecast):
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    return float(np.mean(np.abs((actual - forecast) / actual)) * 100)

# ---------------------------------------------------------------- load
df = pd.read_csv(DATA, parse_dates=["month"])
df = df.sort_values(["segment", "month"]).reset_index(drop=True)
segments = df["segment"].unique().tolist()
last_hist = df["month"].max()
print(f"History: {df['month'].min():%Y-%m} → {last_hist:%Y-%m}, segments: {segments}\n")

backtest_mape = {}
forecast_frames = []
future_idx = pd.date_range(last_hist + pd.offsets.MonthBegin(),
                           periods=FORECAST_MONTHS, freq="MS")

for seg in segments:
    s = df[df["segment"] == seg].set_index("month").sort_index()
    train = s.iloc[:TRAIN_MONTHS]
    holdout = s.iloc[TRAIN_MONTHS:TRAIN_MONTHS + HOLDOUT_MONTHS]

    # --- backtest ---
    seas_tr, mod_tr = seasonal_trend_fit(train[TARGET])
    seas_q, mod_q = seasonal_trend_fit(train["quota"])
    bt_won = forecast_series(train[TARGET], seas_tr, mod_tr, holdout.index)
    backtest_mape[seg] = mape(holdout[TARGET], bt_won)

    # --- refit on full history, forecast 2 quarters ---
    seas_f, mod_f = seasonal_trend_fit(s[TARGET])
    seas_qf, mod_qf = seasonal_trend_fit(s["quota"])
    f_won = forecast_series(s[TARGET], seas_f, mod_f, future_idx)
    f_quota = forecast_series(s["quota"], seas_qf, mod_qf, future_idx)
    # win rate: trailing 6-month mean (stable, explainable)
    f_winrate = float(s["win_rate"].tail(6).mean())

    f = pd.DataFrame({
        "month": future_idx.strftime("%Y-%m"),
        "segment": seg,
        "forecast_won": f_won.to_numpy().round(0).astype(int),
        "forecast_quota": f_quota.to_numpy().round(0).astype(int),
    })
    f["attainment_pct"] = (f["forecast_won"] / f["forecast_quota"] * 100).round(1)
    f["win_rate_assumption"] = round(f_winrate, 4)
    # pipeline coverage needed to hit quota at the assumed win rate
    f["pipeline_needed"] = (f["forecast_quota"] / f_winrate).round(0).astype(int)
    forecast_frames.append(f)

    # --- store series for charts ---
    s.attrs["bt_won"] = bt_won
    s.attrs["f_won"] = f_won
    s.attrs["seas"], s.attrs["mod"] = seas_f, mod_f
    globals()[f"S_{seg.replace('-', '_')}"] = s

forecast = pd.concat(forecast_frames, ignore_index=True)

# ---------------------------------------------------------------- report
print("== Backtest MAPE (train 18mo, hold out last 2 quarters) ==")
for seg in segments:
    print(f"  {seg:12s} MAPE = {backtest_mape[seg]:.1f}%")
overall = float(np.mean(list(backtest_mape.values())))
print(f"  {'Average':12s} MAPE = {overall:.1f}%\n")

att = (forecast.groupby("segment")
       .agg(forecast_won=("forecast_won", "sum"),
            forecast_quota=("forecast_quota", "sum"))
       .assign(attainment_pct=lambda d: (d.forecast_won / d.forecast_quota * 100).round(1)))
print("== H1 2026 forecast attainment (Jan-Jun) ==")
risk = {}
for seg in segments:
    pct = att.loc[seg, "attainment_pct"]
    won, quota = att.loc[seg, "forecast_won"], att.loc[seg, "forecast_quota"]
    status = "AT RISK" if pct < 90 else ("WATCH" if pct < 100 else "ON TRACK")
    risk[seg] = status
    print(f"  {seg:12s} {pct:6.1f}%  (won ${won/1e6:.2f}M / quota ${quota/1e6:.2f}M)  {status}")
print()
print("== Pipeline coverage needed for H1 2026 ==")
for seg in segments:
    sub = forecast[forecast["segment"] == seg]
    wr = sub["win_rate_assumption"].iloc[0]
    need = sub["pipeline_needed"].sum()
    quota = sub["forecast_quota"].sum()
    print(f"  {seg:12s} win rate {wr:.1%} → pipeline needed ${need/1e6:.2f}M "
          f"(quota ${quota/1e6:.2f}M / {wr:.2f})")
print()

# ---------------------------------------------------------------- charts
plt.rcParams.update({"figure.dpi": 150, "font.size": 9})
holdout_start = df["month"].max() - pd.offsets.MonthBegin(HOLDOUT_MONTHS - 1)

fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
for ax, seg in zip(axes, segments):
    s = globals()[f"S_{seg.replace('-', '_')}"]
    ax.plot(s.index, s[TARGET] / 1e6, label="Actual bookings", color="#1f77b4", lw=1.5)
    ax.plot(s.attrs["bt_won"].index, s.attrs["bt_won"].to_numpy() / 1e6,
            label="Backtest forecast", color="#ff7f0e", ls="--", lw=1.5)
    ax.plot(s.attrs["f_won"].index, s.attrs["f_won"].to_numpy() / 1e6,
            label="Forecast (2Q)", color="#2ca02c", lw=2)
    ax.axvspan(holdout_start, last_hist, color="gray", alpha=0.15, label="Holdout")
    ax.axvline(last_hist, color="k", ls=":", lw=1)
    ax.set_title(f"{seg} — actuals vs forecast")
    ax.set_ylabel("$M")
    ax.grid(alpha=0.3)
axes[0].legend(loc="upper left", fontsize=8)
axes[-1].set_xlabel("Month")
fig.suptitle("Pipeline bookings: seasonal-trend forecast (18-mo train, 6-mo backtest)",
             fontsize=11, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS / "forecast_by_segment.png", bbox_inches="tight")
plt.close(fig)

colors = {"AT RISK": "#d62728", "WATCH": "#ff7f0e", "ON TRACK": "#2ca02c"}
fig, ax = plt.subplots(figsize=(8, 4.5))
vals = [att.loc[seg, "attainment_pct"] for seg in segments]
bars = ax.bar(segments, vals, color=[colors[risk[seg]] for seg in segments])
ax.axhline(100, color="k", ls="--", lw=1, label="100% quota")
ax.axhline(90, color="gray", ls=":", lw=1, label="90% risk line")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4, f"{v:.1f}%",
            ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, max(vals) * 1.18)
ax.set_ylabel("Forecast attainment %")
ax.set_title("H1 2026 forecast quota attainment by segment", fontweight="bold")
ax.legend()
fig.tight_layout()
fig.savefig(CHARTS / "attainment_by_segment.png", bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(segments))
need = [forecast[forecast["segment"] == seg]["pipeline_needed"].sum() / 1e6 for seg in segments]
# forecasted pipeline created: scale won forecast by historical created/won ratio
hist_ratio = {seg: float(df[df["segment"] == seg]["pipeline_created"].sum()
                          / df[df["segment"] == seg]["pipeline_won"].sum())
              for seg in segments}
have = [forecast[forecast["segment"] == seg]["forecast_won"].sum() / 1e6 * hist_ratio[seg]
        for seg in segments]
b1 = ax.bar(x - 0.2, need, 0.4, label="Pipeline needed (quota ÷ win rate)", color="#d62728")
b2 = ax.bar(x + 0.2, have, 0.4, label="Pipeline forecast (trend × seasonal)", color="#2ca02c")
ax.set_xticks(x); ax.set_xticklabels(segments)
ax.set_ylabel("$M")
ax.set_title("H1 2026 pipeline coverage: needed vs forecast", fontweight="bold")
for bars_ in (b1, b2):
    for b in bars_:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.15,
                f"${b.get_height():.1f}M", ha="center", fontsize=9)
ax.legend()
fig.tight_layout()
fig.savefig(CHARTS / "coverage_gap.png", bbox_inches="tight")
plt.close(fig)
print("Charts saved to", CHARTS)

# ---------------------------------------------------------------- results.md
lines = ["# Forecast Results — Sales Pipeline & Quota Attainment",
         "",
         "2-quarter forecast (Jan–Jun 2026) from a seasonal-trend decomposition "
         "trained on Jan 2024–Dec 2025. Attainment % = forecast bookings ÷ forecast quota.",
         "",
         "## Backtest accuracy (hold out last 2 quarters)",
         "",
         "| Segment | MAPE |",
         "|---|---|"]
for seg in segments:
    lines.append(f"| {seg} | {backtest_mape[seg]:.1f}% |")
lines += ["", "## Monthly forecast", "",
          "| Month | Segment | Forecast bookings | Forecast quota | Attainment % | "
          "Win-rate assumption | Pipeline needed |",
          "|---|---|---|---|---|---|---|"]
for _, r in forecast.iterrows():
    lines.append(f"| {r['month']} | {r['segment']} | ${r['forecast_won']:,} | "
                 f"${r['forecast_quota']:,} | {r['attainment_pct']:.1f}% | "
                 f"{r['win_rate_assumption']:.1%} | ${r['pipeline_needed']:,} |")
lines += ["", "## H1 2026 summary",
          "",
          "| Segment | Forecast bookings | Forecast quota | Attainment % | Status |",
          "|---|---|---|---|---|"]
for seg in segments:
    lines.append(f"| {seg} | ${att.loc[seg,'forecast_won']:,} | "
                 f"${att.loc[seg,'forecast_quota']:,} | {att.loc[seg,'attainment_pct']:.1f}% | "
                 f"{risk[seg]} |")
lines += ["",
          "_Pipeline needed = forecast quota ÷ trailing 6-month win rate. "
          "Segments below 90% attainment are flagged AT RISK; 90–99% are WATCH._",
          ""]
RESULTS.write_text("\n".join(lines))
print("Wrote", RESULTS)
