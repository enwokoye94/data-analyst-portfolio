# Data Dictionary — Sales Pipeline & Forecast Dashboard

Synthetic CRM dataset generated for portfolio purposes. 2,500 opportunities, 12 sales reps, 3 regions, Jan 2024 – Sep 2026.

## crm_opportunities.csv

| Column | Type | Description |
|---|---|---|
| opportunity_id | string | Unique opportunity key, e.g. OPP-00001 |
| account_id | string | Account key, e.g. Acct-0057 (180 distinct accounts) |
| rep_id | string | Owning sales rep, joins to sales_reps.rep_id |
| region | string | West / Central / East (denormalized from rep) |
| stage | string | Pipeline stage: Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost |
| amount | numeric | Opportunity value in USD |
| created_date | date | Date the opportunity was created (YYYY-MM-DD) |
| close_date | date | Actual or expected close date (YYYY-MM-DD) |
| forecast_category | string | Commit / Best Case / Pipeline / Omitted |

## sales_reps.csv

| Column | Type | Description |
|---|---|---|
| rep_id | string | Unique rep key, e.g. R001 |
| rep_name | string | Rep full name |
| region | string | West / Central / East (4 reps each) |
| annual_quota | numeric | Annual sales quota in USD |

## Suggested Power BI model

- **Opportunities** fact table (crm_opportunities) → **Sales Reps** dimension on rep_id (single direction)
- **Date** dimension table (build with CALENDAR) joined to close_date for time intelligence; mark as date table
- Hide rep_id on the fact; expose rep_name / region from the dimension
