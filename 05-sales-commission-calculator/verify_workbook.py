"""
Verifies commission_calculator.xlsx:
1. Reopens the workbook; asserts key formula cells contain the expected
   formula patterns (correct functions + named ranges), not hardcoded values.
2. Independently recomputes every KPI in Python from data/deals.csv using the
   same plan parameters, and prints the results (used for README findings).
"""
import csv
import re
from pathlib import Path
from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent

PLAN = dict(t1=0.05, t2=0.08, t3=0.12, accel=0.02,
            accel_mult=1.25, t2_mult=1.5, spiff=500, draw=9000)

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]


def plan_payout(revenue, quota, new_logos):
    t1 = min(revenue, quota) * PLAN["t1"]
    t2 = max(min(revenue, quota * PLAN["t2_mult"]) - quota, 0) * PLAN["t2"]
    t3 = max(revenue - quota * PLAN["t2_mult"], 0) * PLAN["t3"]
    acc = max(revenue - quota * PLAN["accel_mult"], 0) * PLAN["accel"]
    spiff = new_logos * PLAN["spiff"]
    comm = t1 + t2 + t3 + acc + spiff
    return comm, max(comm, PLAN["draw"])


def main():
    deals = list(csv.DictReader(open(BASE / "data" / "deals.csv")))
    reps = list(csv.DictReader(open(BASE / "data" / "reps.csv")))

    # ---- 1. formula spot checks ----
    wb = load_workbook(BASE / "commission_calculator.xlsx")
    wr = wb["Rep Summary"]
    wd = wb["Dashboard"]
    wp = wb["Plan"]

    expected = {
        "E2 revenue":      "=SUMIFS(d_size,d_rep,A2,d_qtr,C2)",
        "F2 attainment":   "=IF(D2=0,0,E2/D2)",
        "G2 tier1":        "=MIN(E2,D2)*rate_t1",
        "H2 tier2":        "=MAX(MIN(E2,D2*t2_mult)-D2,0)*rate_t2",
        "I2 tier3":        "=MAX(E2-D2*t2_mult,0)*rate_t3",
        "J2 accelerator":  "=MAX(E2-D2*accel_mult,0)*rate_accel",
        "K2 new-logo cnt": '=COUNTIFS(d_rep,A2,d_qtr,C2,d_newlogo,"Y")',
        "L2 spiff":        "=K2*spiff_amt",
        "M2 total comm":   "=G2+H2+I2+J2+L2",
        "O2 payout":       "=MAX(M2,N2)",
    }
    cells = {"E2": wr["E2"], "F2": wr["F2"], "G2": wr["G2"], "H2": wr["H2"],
             "I2": wr["I2"], "J2": wr["J2"], "K2": wr["K2"], "L2": wr["L2"],
             "M2": wr["M2"], "O2": wr["O2"]}
    ok = True
    for label, exp in expected.items():
        key = label.split()[0]
        val = cells[key].value
        good = isinstance(val, str) and re.fullmatch(re.escape(exp), val) is not None
        ok &= good
        print(f"[{'OK' if good else 'FAIL'}] {label}: {val}")
    for label, cell, exp in [
        ("Plan B11 qdraw", wp["B11"], "=B9*3"),
        ("Dash total rev", wd["B4"], "=SUM(d_size)"),
        ("Dash payout", wd["B6"], "=SUM(rs_payout)"),
        ("Dash top earner", wd["B11"], "=INDEX(rs_rep,MATCH(MAX(rs_payout),rs_payout,0))"),
        ("Dash draw cases", wd["B10"], "=SUMPRODUCT(--(rs_comm<qtr_draw))"),
    ]:
        val = cell.value
        good = isinstance(val, str) and re.fullmatch(re.escape(exp), val) is not None
        ok &= good
        print(f"[{'OK' if good else 'FAIL'}] {label}: {val}")

    # every Rep Summary row must be a formula (no hardcoded payouts)
    formula_cols = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]
    hardcoded = [(c, r) for r in range(2, 50) for c in formula_cols
                 if not str(wr[f"{c}{r}"].value).startswith("=")]
    print(f"[{'OK' if not hardcoded else 'FAIL'}] all 48x13 calc cells are formulas"
          + (f" — {len(hardcoded)} hardcoded!" if hardcoded else ""))

    # ---- 2. independent Python recomputation ----
    rows = []
    for rep in reps:
        quota = int(rep["quarterly_quota"])
        for q in QUARTERS:
            rd = [d for d in deals if d["rep_name"] == rep["rep_name"] and d["quarter"] == q]
            rev = sum(int(d["deal_size"]) for d in rd)
            nl = sum(1 for d in rd if d["new_logo"] == "Y")
            comm, payout = plan_payout(rev, quota, nl)
            att = rev / quota
            band = ("≥150%" if att >= 1.5 else "125-149%" if att >= 1.25
                    else "100-124%" if att >= 1 else "80-99%" if att >= 0.8 else "<80%")
            rows.append(dict(rep=rep["rep_name"], q=q, rev=rev, quota=quota,
                             att=att, comm=comm, payout=payout, nl=nl, band=band))

    total_rev = sum(r["rev"] for r in rows)
    total_comm = sum(r["comm"] for r in rows)
    total_payout = sum(r["payout"] for r in rows)
    total_spiff = sum(r["nl"] for r in rows) * PLAN["spiff"]
    draw_cases = sum(1 for r in rows if r["comm"] < PLAN["draw"])
    top_q = max(rows, key=lambda r: r["payout"])
    annual = {}
    for r in rows:
        annual[r["rep"]] = annual.get(r["rep"], 0) + r["payout"]
    top_rep = max(annual, key=annual.get)
    bands = {}
    for r in rows:
        bands[r["band"]] = bands.get(r["band"], 0) + 1

    print("\n--- independent recomputation (README numbers) ---")
    print(f"deals={len(deals)} total_rev={total_rev:,}")
    print(f"total_commission_pre_draw={total_comm:,.0f}")
    print(f"total_payout={total_payout:,.0f}")
    print(f"payout_pct_of_revenue={total_payout/total_rev:.1%}")
    print(f"avg_attainment={sum(r['att'] for r in rows)/len(rows):.1%}")
    print(f"total_spiffs={total_spiff:,}  draw_cases={draw_cases}")
    print(f"top_quarter: {top_q['rep']} {top_q['q']} payout={top_q['payout']:,.0f} att={top_q['att']:.0%}")
    print(f"top_annual: {top_rep} payout={annual[top_rep]:,.0f}")
    print("bands:", {k: bands.get(k, 0) for k in ["<80%", "80-99%", "100-124%", "125-149%", "≥150%"]})
    print("quarterly payout:", {q: f"{sum(r['payout'] for r in rows if r['q']==q):,.0f}" for q in QUARTERS})

    assert ok and not hardcoded, "formula verification failed"


if __name__ == "__main__":
    main()
