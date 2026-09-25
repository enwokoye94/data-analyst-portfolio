# Order Operations Analysis (SQL)

Fulfillment performance analysis on a 5,000-order synthetic dataset — the same questions an operations analyst answers from Salesforce/ERP order data every week.

## Business questions

1. **On-time delivery by region** — where are we missing promised dates?
2. **Rep leaderboard** — revenue rank vs. reliability rank (window functions); the top closer isn't always the most reliable
3. **Late-shipment trend** — monthly late % with a running total to spot deterioration early
4. **Open backlog** — oldest unshipped orders and dollars at risk
5. **Cancellations by segment** — which customer tier cancels most

## Schema

- **orders** (5,000 rows): order_id, customer_id, rep_id, product_id, quantity, unit_price, order_date, promised_date, ship_date, status
- **customers** (300): customer_id, customer_name, region, segment
- **reps** (10): rep_id, rep_name, region

## How to run

```bash
sqlite3 orders.db < analysis.sql
```

All queries use standard SQL (CTEs, window functions, date math) portable to SQL Server, Postgres, Snowflake, and BigQuery.

## Key findings (see results.md)

- On-time delivery sits at **63–66%** across regions — the South is slowest at 7.4 avg fulfillment days
- The #1 rep by revenue ranks only #5 on reliability — a coaching opportunity, not a compensation one
- Late shipments run ~27–33% monthly with no clear improvement trend — a process problem, not a seasonal one

## Skills demonstrated

SQL (CTEs, RANK(), running totals, conditional aggregation) · translating business questions into queries · operations domain knowledge (OTD, backlog, fulfillment SLAs)

*All data is synthetic and generated for portfolio purposes.*
