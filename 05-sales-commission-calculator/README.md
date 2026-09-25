# Sales Commission Calculator (Excel)

**The problem:** compensation is a sales organization's biggest controllable expense — and its most error-prone spreadsheet. Reps don't trust payouts they can't audit, finance can't close the books on manual math, and every plan change means rebuilding the model. In sales operations, the commission workbook *is* the trust layer between the company and its sellers.

This workbook is a fully formula-driven commission engine: change any plan parameter on the **Plan** sheet and all 48 rep-quarter payouts, the dashboard, and the charts recalculate instantly. No hardcoded payouts anywhere.

## The plan design

A classic tiered + accelerator structure, the kind sales ops actually administers:

| Component | Design |
|---|---|
| Tier 1 | 5% on revenue from 0–100% of quota |
| Tier 2 | 8% on revenue from 100–150% of quota (marginal) |
| Tier 3 | 12% on revenue above 150% of quota (marginal) |
| Accelerator | Extra 2% on all revenue above 125% of quota (stacks with tiers) |
| New-logo spiff | $500 per new-logo deal, on top of tiered commission |
| Draw | $3,000/month recoverable — quarterly payout is `MAX(commission, $9,000)` |

Marginal tiers matter: paying the higher rate only on the dollars *above* each threshold is what keeps the plan affordable while still rewarding over-performance. All thresholds and rates are named ranges on the Plan sheet, so leadership can scenario-model ("what if tier 2 were 9%?") without touching a formula.

## How the workbook works

- **Deals** — 531 synthetic closed-won deals (12 reps × 4 quarters, FY2025): deal ID, rep, region, quarter, product line, deal size, new-logo flag. AutoFilter on, frozen header.
- **Plan** — every parameter in blue editable cells; quarterly draw is itself a formula (`=B9*3`). Notes explain the plan mechanics.
- **Rep Summary** — 48 rep-quarter rows. Revenue via `SUMIFS` on the Deals table; tier splits with `MIN`/`MAX` marginal math; new-logo count via `COUNTIFS`; payout via `MAX(commission, draw)`; attainment band via nested `IF`. Attainment column has traffic-light conditional formatting (green ≥100%, amber 80–99%, red <80%).
- **Dashboard** — total payout, payout as % of revenue, average attainment, spiff totals, draw cases, top earners (single quarter + annual via `INDEX/MATCH` on `MAX`), attainment distribution, quarterly payout — plus a bar chart and a pie chart.

Key formulas used: `SUMIFS`, `COUNTIFS`, `SUMPRODUCT` (draw-case count), `INDEX` + `MATCH`, `MAX`/`MIN` marginal-tier math, nested `IF`, named ranges throughout.

## Key findings (from the verified run)

| Metric | Value |
|---|---|
| Total revenue (531 deals) | **$14,783,358** |
| Total commission earned (pre-draw) | **$853,900** |
| Total payout (after draw guarantee) | **$854,515** |
| Payout as % of revenue | **5.8%** |
| Average attainment (48 rep-quarters) | **99.2%** |
| New-logo spiffs paid (130 new-logo deals) | **$65,000** |
| Rep-quarters paid at draw | 1 |
| Top single-quarter earner | **Daniel Okafor — Q1, $34,862** (151% attainment) |
| Top annual earner | **Daniel Okafor — $111,708** |
| Attainment distribution | <80%: 12 · 80–99%: 11 · 100–124%: 19 · 125–149%: 5 · ≥150%: 1 |

What the numbers say: the plan is healthy — average attainment sits right at quota (99.2%), only 1 of 48 rep-quarters fell back on the draw guarantee, and the top earner took home $111,708 on the year. But the left tail is real: 12 rep-quarters under 80% (concentrated in two reps) is a coaching/management signal, and the 125%+ club (6 rep-quarters) is where the accelerator dollars concentrate.

## Files

- `commission_calculator.xlsx` — the workbook (open it; everything calculates)
- `generate_data.py` — synthetic data generator (seed 42) → `data/deals.csv`, `data/reps.csv`
- `build_workbook.py` — rebuilds the workbook from the CSVs, formulas included
- `verify_workbook.py` — reopens the .xlsx, asserts 15 key formulas match exactly, confirms all 624 calculated cells are formulas (zero hardcoded values), and independently recomputes every KPI in Python
- `data_dictionary.md` — field definitions

## Skills demonstrated

Advanced Excel (SUMIFS/COUNTIFS, marginal-tier math, INDEX/MATCH, SUMPRODUCT, named ranges, conditional formatting, charts) · sales compensation design (tiers, accelerators, spiffs, draws) · payout auditability · Python + openpyxl automation

*All data is synthetic and generated for portfolio purposes (seed 42).*
