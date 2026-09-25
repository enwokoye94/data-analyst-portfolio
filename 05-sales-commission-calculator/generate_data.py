"""
Synthetic closed-won deal generator for the Sales Commission Calculator portfolio project.

Creates:
    data/deals.csv  ~600 closed-won deals across 12 reps x 4 quarters (2025)
    data/reps.csv   rep roster with region + quarterly quota

All data is SYNTHETIC — generated with a fixed seed for reproducibility.
No real company, rep, or customer data is used.
"""
import csv
import random
from pathlib import Path

SEED = 42
OUT_DIR = Path(__file__).resolve().parent / "data"

# rep_name, region, quarterly_quota, performance factor (avg attainment target)
REPS = [
    ("Marcus Webb",   "West",    350_000, 1.25),
    ("Priya Raman",   "West",    350_000, 1.10),
    ("Jordan Ellis",  "West",    300_000, 0.95),
    ("Sofia Delgado", "Central", 300_000, 1.05),
    ("Tyler Brooks",  "Central", 300_000, 0.85),
    ("Aisha Khan",    "Central", 275_000, 1.15),
    ("Daniel Okafor", "East",    350_000, 1.30),
    ("Lena Fischer",  "East",    325_000, 1.00),
    ("Chris Novak",   "East",    300_000, 0.80),
    ("Maria Santos",  "South",   300_000, 1.12),
    ("James Park",    "South",   275_000, 0.90),
    ("Nina Petrova",  "South",   250_000, 0.70),
]

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# product_line, weight, median deal size
PRODUCTS = [
    ("Core Platform",    0.50, 12_000),
    ("Enterprise Suite", 0.20, 55_000),
    ("Add-on Services",  0.30,  6_000),
]

NEW_LOGO_PROB = 0.25


def pick_product(rng):
    r = rng.random()
    cum = 0.0
    for name, weight, median in PRODUCTS:
        cum += weight
        if r <= cum:
            return name, median
    return PRODUCTS[-1][0], PRODUCTS[-1][2]


def deal_size(rng, median):
    # lognormal-ish spread around the product median, rounded to $100
    size = rng.lognormvariate(__import__("math").log(median), 0.55)
    return max(1_000, int(round(size / 100) * 100))


def main():
    rng = random.Random(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    deals = []
    deal_n = 0
    for rep_name, region, quota, factor in REPS:
        for quarter in QUARTERS:
            # target attainment for this rep-quarter, centered on the rep's factor
            target_att = min(1.75, max(0.45, rng.gauss(factor, 0.12)))
            target_rev = target_att * quota

            n_deals = max(6, int(rng.gauss(12.5, 2.5)))
            raw = []
            for _ in range(n_deals):
                product, median = pick_product(rng)
                raw.append((product, deal_size(rng, median)))

            raw_total = sum(s for _, s in raw) or 1
            scale = target_rev / raw_total
            for product, size in raw:
                deal_n += 1
                new_logo = "Y" if rng.random() < NEW_LOGO_PROB else "N"
                deals.append({
                    "deal_id": f"D-{deal_n:04d}",
                    "rep_name": rep_name,
                    "region": region,
                    "quarter": quarter,
                    "product_line": product,
                    "deal_size": int(round(size * scale)),
                    "new_logo": new_logo,
                })

    with open(OUT_DIR / "deals.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["deal_id", "rep_name", "region",
                                          "quarter", "product_line",
                                          "deal_size", "new_logo"])
        w.writeheader()
        w.writerows(deals)

    with open(OUT_DIR / "reps.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rep_name", "region", "quarterly_quota"])
        for rep_name, region, quota, _ in REPS:
            w.writerow([rep_name, region, quota])

    total_rev = sum(d["deal_size"] for d in deals)
    print(f"deals.csv: {len(deals)} deals, ${total_rev:,} total revenue")
    print(f"reps.csv:  {len(REPS)} reps")


if __name__ == "__main__":
    main()
