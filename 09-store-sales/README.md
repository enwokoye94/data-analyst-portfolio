# Store Sales Analysis (Python)

End-to-end retail sales analysis: 12 monthly extracts consolidated into a single
dataset, cleaned, feature-engineered, and visualized to answer "when and where do
we sell the most?"

**Notebook:** `Sales Anlysis.ipynb` — runs clean top-to-bottom (pandas 3, seaborn 0.13).

## What was done
- Consolidated 12 monthly CSVs with a single `pd.concat` (replacing a slow loop)
- Parsed city/state from address strings; engineered month, hour, and weekday features
- Built monthly revenue trend, city/state rankings, and hourly order heatmaps

## Key findings
- **December** is the strongest month: **$4.61M** in sales (clear holiday spike)
- **San Francisco** leads all cities at **$8.25M**
- **California** leads all states at **$13.7M**

## Skills
Python, pandas, matplotlib/seaborn, data cleaning, EDA, time-series aggregation

*Source: original project at github.com/enwokoye94/Store-Sales. Notebook verified and
repaired — see the portfolio's `FIXES.md` notes.*
