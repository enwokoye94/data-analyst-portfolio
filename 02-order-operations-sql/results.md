# Query Results (verified)

## Q1: On-time delivery rate and avg fulfillment days by region

| region | shipped_orders | on_time_pct | avg_fulfill_days |
| --- | --- | --- | --- |
| Northeast | 945 | 65.5 | 6.9 |
| West | 948 | 64.1 | 6.8 |
| South | 972 | 63.8 | 7.4 |
| Midwest | 1053 | 62.8 | 7.1 |

## Q2: Rep leaderboard — revenue, on-time %, and rank (window functions)

| rep_name | region | orders_handled | revenue | on_time_pct | revenue_rank | reliability_rank |
| --- | --- | --- | --- | --- | --- | --- |
| M. Patel | West | 432 | 1511442.32 | 64.6 | 1 | 5 |
| E. Wilson | Midwest | 421 | 1447177.46 | 65.1 | 2 | 4 |
| N. Brooks | Northeast | 391 | 1408917.8 | 62.7 | 3 | 7 |
| S. Reyes | Northeast | 402 | 1385207.31 | 62.7 | 4 | 6 |
| E. Cole | Northeast | 384 | 1384469.94 | 68.0 | 5 | 1 |
| A. Thompson | South | 391 | 1332751.09 | 61.4 | 6 | 9 |
| P. Nair | South | 384 | 1317700.01 | 66.4 | 7 | 2 |
| L. Gray | Northeast | 389 | 1301990.95 | 61.2 | 8 | 10 |
| J. Park | Northeast | 368 | 1287222.31 | 66.0 | 9 | 3 |
| L. Carter | Midwest | 356 | 1169624.63 | 62.1 | 10 | 8 |

## Q3: Monthly late-shipment trend (CTE + running total)

| month | total_orders | late_orders | late_pct | running_late_total |
| --- | --- | --- | --- | --- |
| 2024-01 | 179 | 59 | 33.0 | 59 |
| 2024-02 | 168 | 47 | 28.0 | 106 |
| 2024-03 | 177 | 47 | 26.6 | 153 |
| 2024-04 | 186 | 55 | 29.6 | 208 |
| 2024-05 | 186 | 34 | 18.3 | 242 |
| 2024-06 | 165 | 55 | 33.3 | 297 |
| 2024-07 | 198 | 58 | 29.3 | 355 |
| 2024-08 | 191 | 51 | 26.7 | 406 |
| 2024-09 | 203 | 54 | 26.6 | 460 |
| 2024-10 | 180 | 51 | 28.3 | 511 |
| 2024-11 | 195 | 45 | 23.1 | 556 |
| 2024-12 | 194 | 46 | 23.7 | 602 |

*15 more rows omitted*

## Q4: Open backlog — oldest unshipped orders and their value at risk

| order_id | customer_name | region | rep_name | order_date | promised_date | days_open | order_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-00534 | Customer 119 | Northeast | E. Wilson | 2024-01-02 | 2024-01-07 | 997 | 1429.89 |
| ORD-03185 | Customer 110 | South | S. Reyes | 2024-01-03 | 2024-01-08 | 996 | 359.96 |
| ORD-03517 | Customer 188 | South | P. Nair | 2024-01-03 | 2024-01-06 | 996 | 4899.86 |
| ORD-01350 | Customer 130 | Midwest | E. Cole | 2024-01-05 | 2024-01-10 | 994 | 499.98 |
| ORD-03471 | Customer 239 | South | A. Thompson | 2024-01-08 | 2024-01-15 | 991 | 1799.8 |
| ORD-00828 | Customer 223 | Midwest | N. Brooks | 2024-01-13 | 2024-01-23 | 986 | 5249.85 |
| ORD-01622 | Customer 114 | Northeast | J. Park | 2024-01-13 | 2024-01-18 | 986 | 1819.86 |
| ORD-00548 | Customer 115 | Northeast | A. Thompson | 2024-01-16 | 2024-01-23 | 983 | 2499.9 |
| ORD-00209 | Customer 30 | South | S. Reyes | 2024-01-17 | 2024-01-27 | 982 | 10499.79 |
| ORD-02838 | Customer 217 | Midwest | P. Nair | 2024-01-18 | 2024-01-23 | 981 | 3499.9 |
| ORD-02935 | Customer 224 | West | L. Gray | 2024-01-18 | 2024-01-21 | 981 | 5499.89 |
| ORD-02255 | Customer 183 | West | E. Wilson | 2024-01-19 | 2024-01-22 | 980 | 5249.85 |

*3 more rows omitted*

## Q5: Cancellation rate by customer segment

| segment | total_orders | cancelled | cancel_pct |
| --- | --- | --- | --- |
| Enterprise | 1850 | 209 | 11.3 |
| Mid-Market | 1513 | 142 | 9.4 |
| SMB | 1637 | 149 | 9.1 |
