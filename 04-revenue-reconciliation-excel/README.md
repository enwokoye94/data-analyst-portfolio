# Revenue Reconciliation Case Study (Excel)

Month-end close problem: the billing system and the ERP disagree. This workbook reconciles 122 invoices across both sources with a fully formula-driven workflow — no manual matching.

## The setup

- **Billing_Extract** — 120 invoices from the billing system
- **ERP_Extract** — the ERP's version: 3 invoices missing, 5 amounts altered, 2 ERP-only invoices
- **Reconciliation** — union of all invoice IDs; INDEX/MATCH pulls each amount; variance and status are pure formulas
- **Summary** — counts, totals, net variance, match rate (all formulas), plus an outcome chart

## What it catches

| Outcome | Count |
|---|---|
| ✓ Matched | 112 |
| ⚠ Investigate (amount variance) | 5 |
| Missing in ERP | 3 |
| Missing in Billing | 2 |

## Techniques used

- **INDEX + MATCH** instead of VLOOKUP — survives column inserts, works left-to-right or right-to-left
- **IFERROR** guards so a missing invoice shows "—" instead of #N/A noise
- **Nested IF** status logic: missing-in-source vs. amount variance get different treatments
- **Conditional formatting** — green/red/amber status highlighting that updates live
- **COUNTIF / SUMIF** summary layer, so the dashboard never needs manual refreshing

## Why this matters in sales/revenue operations

Reconciliation is the unglamorous control behind every revenue number leadership trusts. A repeatable, formula-driven recon beats a monthly manual eyeball-check on accuracy, auditability, and time.

## Skills demonstrated

Advanced Excel (INDEX/MATCH, nested IF, IFERROR, conditional formatting) · financial controls thinking · reconciliation design

*All data is synthetic and generated for portfolio purposes.*
