# Airbnb Listings Data Exploration (Python)

Large-scale exploratory analysis of Airbnb listing, calendar, and review data —
**1,059,288 listings, ~17M calendar rows, ~1.06M reviews**.

**Notebook:** `Data Exploration.ipynb` — runs clean top-to-bottom (pandas 3).

## What was done
- Profiled missingness across all three datasets and built reusable `obs_data` / `clean_data` helpers
- Cleaned price strings (`$1,234.00` → float), parsed dates, engineered year/month features
- Split host-level vs. rental-level attributes into separate analysis frames
- Encoded categorical host attributes for downstream modeling

## Key findings
- Calendar table dominates at ~17M rows / ~1.1 GB in memory — drove the decision to clean in a streaming-friendly, column-selective way
- Price and availability fields required the most cleaning (currency strings, mixed types)
- Produced clean, analysis-ready host and rental feature sets from the raw extracts

## Skills
Python, pandas (large-data handling), data cleaning, feature engineering, EDA

*Source: original project at github.com/enwokoye94/AirBnB-. Data files are Git-LFS hosted;
run `git lfs pull` after cloning. Notebook verified and repaired — see the portfolio's
`FIXES.md` notes.*
