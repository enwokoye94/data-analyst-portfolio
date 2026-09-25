#!/usr/bin/env python3
"""
Synthetic data generator for the RFM Customer Segmentation portfolio project.

Creates data/customers.db (SQLite) with:
  - customers(customer_id, name, segment_hint, signup_date, region)   ~2,000 rows
  - transactions(txn_id, customer_id, txn_date, amount)               ~25,000 rows

All data is synthetic. Fixed seeds make every run reproducible.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

OUT = Path(__file__).resolve().parent / "data" / "customers.db"

# Fixed analysis window — keeps the SQL "as of" date reproducible.
AS_OF = date(2026, 9, 30)
WINDOW_START = date(2024, 10, 1)

FIRST = ["Ava", "Liam", "Maya", "Noah", "Zoe", "Ethan", "Priya", "Lucas", "Nora",
         "Owen", "Ivy", "Caleb", "Ruby", "Miles", "Ella", "Jonah", "Sofia",
         "Derek", "Lena", "Omar", "Tara", "Felix", "Nina", "Hugo", "Aisha",
         "Ben", "Clara", "Dev", "Elsa", "Finn", "Gia", "Hank", "Isla", "Jude",
         "Kira", "Leo", "Mila", "Nate", "Opal", "Paul", "Quinn", "Rosa",
         "Sam", "Tessa", "Uma", "Vince", "Wren", "Xander", "Yara", "Zane"]
LAST = ["Carter", "Nguyen", "Patel", "Garcia", "Kim", "Okafor", "Smith",
        "Rivera", "Chen", "Brooks", "Haddad", "Lopez", "Singh", "Murphy",
        "Khan", "Silva", "Adams", "Baker", "Cole", "Diaz", "Evans", "Ford",
        "Grant", "Hayes", "Iqbal", "Jones", "Katz", "Lane", "Moss", "Nash",
        "Owens", "Park", "Reed", "Stone", "Turner", "Vance", "Ward", "Young",
        "Zhang", "Bell", "Cox", "Dunn", "Ellis", "Frost", "Gray", "Hall",
        "Irwin", "Jennings", "Kerr", "Lloyd", "Meyer", "Nolan", "Osborne",
        "Pruitt", "Quill", "Rivas", "Sutton", "Talley", "Underwood", "Vaughan"]

REGIONS = ["Northeast", "Midwest", "South", "West"]

# (hint, share, txn_range, amount_mean, amount_sigma, last_txn_days_ago_range, span_days)
ARCHETYPES = [
    ("champion",     0.08, (22, 48), 800,  0.70, (0, 30),    500),
    ("loyal",        0.15, (13, 28), 450,  0.80, (0, 60),    600),
    ("potential",    0.12, (6, 13),  350,  0.90, (0, 90),    300),
    ("new",          0.10, (1, 4),   300,  0.90, (0, 45),    45),
    ("at_risk",      0.12, (7, 16),  500,  0.80, (120, 300), 450),
    ("hibernating",  0.13, (3, 9),   280,  0.90, (200, 500), 300),
    ("lost",         0.20, (2, 5),   220,  1.00, (400, 700), 200),
    ("cant_lose",    0.05, (17, 33), 1200, 0.60, (150, 350), 500),
    ("need_attention", 0.05, (4, 9), 320,  0.90, (90, 180),  250),
]

N_CUSTOMERS = 2000


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    con = sqlite3.connect(OUT)
    cur = con.cursor()
    cur.execute("""CREATE TABLE customers(
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        segment_hint TEXT NOT NULL,
        signup_date TEXT NOT NULL,
        region TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE transactions(
        txn_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        txn_date TEXT NOT NULL,
        amount REAL NOT NULL)""")

    hints = [a[0] for a in ARCHETYPES]
    weights = [a[1] for a in ARCHETYPES]
    chosen = rng.choice(hints, size=N_CUSTOMERS, p=weights)
    arch = {a[0]: a for a in ARCHETYPES}

    txn_id = 0
    cust_rows, txn_rows = [], []
    for cid, hint in enumerate(chosen, start=1):
        _, _, txn_range, amt_mean, amt_sigma, last_range, span = arch[hint]
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        region = random.choice(REGIONS)
        last_ago = int(rng.integers(last_range[0], last_range[1] + 1))
        last_date = AS_OF - timedelta(days=last_ago)
        signup = max(WINDOW_START,
                     last_date - timedelta(days=int(rng.integers(30, span + 60))))
        cust_rows.append((cid, name, hint, signup.isoformat(), region))

        n_txn = int(rng.integers(txn_range[0], txn_range[1] + 1))
        earliest = max(WINDOW_START, last_date - timedelta(days=span))
        for _ in range(n_txn):
            span_days = max((last_date - earliest).days, 1)
            d = earliest + timedelta(days=int(rng.integers(0, span_days + 1)))
            d = min(d, last_date)  # keep the recency profile exact
            amount = round(float(rng.lognormal(np.log(amt_mean), amt_sigma)), 2)
            amount = max(amount, 10.0)
            txn_id += 1
            txn_rows.append((txn_id, cid, d.isoformat(), amount))

    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", cust_rows)
    cur.executemany("INSERT INTO transactions VALUES (?,?,?,?)", txn_rows)
    cur.execute("CREATE INDEX idx_txn_customer ON transactions(customer_id)")
    cur.execute("CREATE INDEX idx_txn_date ON transactions(txn_date)")
    con.commit()

    n_c = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    n_t = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    rev = cur.execute("SELECT ROUND(SUM(amount),2) FROM transactions").fetchone()[0]
    con.close()
    print(f"wrote {OUT}: {n_c} customers, {n_t} transactions, ${rev:,.2f} revenue")


if __name__ == "__main__":
    main()
