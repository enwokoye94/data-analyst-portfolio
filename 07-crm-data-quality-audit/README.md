# CRM Data-Quality Audit — Python

> **One-liner:** A reusable Python audit toolkit that scores CRM hygiene (0–100), finds the exact rows breaking your forecast, and produces a cleaned export. Built on a synthetic 5,000-opportunity Salesforce-style extract with realistic data-quality problems baked in.

---

## The business problem

Sales Operations lives or dies on CRM data quality. When the pipeline data is dirty, everything downstream is wrong:

- **Forecasts** overstate commit because duplicate opportunities double-count the same deal.
- **Win-rate and cycle-length reporting** breaks when stages are spelled 26 different ways ("Closed Won" vs "Closed-Won" vs "closed won").
- **Territory and quota reporting** misattributes revenue when owner IDs don't match any real rep.
- **Marketing attribution** rots when contact emails are invalid.

This project simulates the exact diagnostic a Sales Ops analyst runs during a CRM hygiene initiative: pull the export, measure what's broken, quantify the business impact, and ship a cleaned dataset with remediation recommendations.

## Methodology

`audit.py` is written as a **reusable toolkit** (functions, not one-off spaghetti) — point it at any opportunity-style CSV and it runs the same battery:

| Check | What it does |
|---|---|
| **Completeness** | % non-blank values per field |
| **Duplicates** | Groups rows on a normalized `(account, amount, close_date)` key — case/whitespace/format-insensitive, so `"$12,500"` and `"12500.00"` still match |
| **Email validity** | RFC-style regex on non-blank contact emails |
| **Stage standardization** | Maps 26 raw variants → 5 canonical stages via a lookup table; reports anything unmapped |
| **Date sanity** | Flags future `created_date`s, `close_date < created_date`, and unparseable dates |
| **Owner integrity** | Flags owner IDs absent from the active roster (orphans) |
| **Hygiene score** | Starts at 100, subtracts capped penalties per issue class → 0–100 with an A–F grade |

The cleaner then **deduplicates, standardizes stages, parses amounts/dates into typed columns**, and keeps the raw values alongside so every transformation is auditable.

## Key findings (from the actual run, seed = 42)

**Overall hygiene: 71.4/100 (grade C) → 83.2/100 after cleaning.**

| Finding | Number | Business impact |
|---|---|---|
| Duplicate opportunities | **294 rows (5.88%)** across 279 duplicate groups | Same deal counted twice → inflated pipeline and forecast |
| Worst completeness: `close_date` | **6.24% missing** | Deals with no close date can't be forecasted or aged |
| Missing `amount` | **4.68% missing** | Pipeline value understated |
| Missing `stage` | **4.30% missing** | Deals invisible to stage-based reporting |
| Invalid contact emails | **132** | Broken outreach, bad attribution |
| Stage-name variants | **26 raw spellings → 5 canonical** | Win-rate/funnel reports unreliable until mapped |
| Future `created_date`s | **70 rows** (bad integration backfill — most also have `close_date` *before* `created_date`) | Corrupts cycle-length and sourcing metrics |
| Orphaned owner IDs | **138 rows (2.76%)** | Revenue misattributed in territory reporting |

**Duplicates concentrate in "Bulk Import"** — the classic culprit: re-imported lists creating dupes. (See `charts/duplicates_by_source.png`.)

The residual 16.8 points after cleaning are almost entirely **missing values**, which no script can fix — that requires process change (validation rules at entry).

## Remediation recommendations

1. **Dedupe job on import** — match on `(account, amount, close_date)` before any bulk load; the Bulk Import source alone created most dupes.
2. **Lock down the Stage picklist** — 26 variants for 5 stages means reps are free-typing; restrict to the canonical list and migrate history with the provided map.
3. **Required-field validation** — make `close_date`, `amount`, and `stage` required on create; 4–6% missingness is a data-entry governance problem.
4. **Owner roster sync** — 138 rows point at dead/invalid user IDs; reassign and add a validation against the active user table.
5. **Fix the integration backfill** — the 70 future `created_date`s came from a bad backfill; quarantine and re-run with correct timestamps.
6. **Email validation at capture** — 132 invalid emails caught by a one-line regex that should live in the web form.

## Skills demonstrated

- Python data wrangling (pandas), regex validation, date/amount parsing
- Designing a **composite data-quality score** with explainable penalties
- Building a **reusable audit toolkit** (generic check functions, CLI entry point)
- Root-cause analysis tying data issues to business metrics (forecast, attribution, reporting)
- matplotlib reporting (missingness heatmap-style bars, gauge chart, source breakdown)

## Files

| File | Description |
|---|---|
| `generate_data.py` | Synthetic data generator (seed 42) — creates the messy export |
| `audit.py` | The reusable audit + cleaning toolkit |
| `data/crm_export_messy.csv` | Input: 5,000 messy opportunity records |
| `data/crm_export_clean.csv` | Output: 4,706 deduplicated, standardized records |
| `data/audit_findings.json` | Machine-readable findings |
| `data_dictionary.md` | Field definitions + cleaning rules |
| `charts/` | `missingness_by_field.png`, `hygiene_score.png`, `duplicates_by_source.png` |

## Reproduce it

```bash
python3 generate_data.py   # rebuild the messy export (fixed seed → identical output)
python3 audit.py           # run the audit, write clean file + charts + findings JSON
```

---

*All data is synthetic and generated with a fixed random seed. No real company or customer data is used.*
