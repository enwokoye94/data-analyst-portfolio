-- Order Operations Analysis
-- SQLite. Business questions an operations analyst answers from order data.

-- Q1: On-time delivery rate and avg fulfillment days by region
WITH shipped AS (
    SELECT o.*, c.region,
           julianday(o.ship_date) - julianday(o.order_date) AS fulfill_days,
           CASE WHEN o.ship_date <= o.promised_date THEN 1 ELSE 0 END AS on_time
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'Shipped'
)
SELECT region,
       COUNT(*) AS shipped_orders,
       ROUND(AVG(on_time) * 100, 1) AS on_time_pct,
       ROUND(AVG(fulfill_days), 1) AS avg_fulfill_days
FROM shipped
GROUP BY region
ORDER BY on_time_pct DESC;

-- Q2: Rep leaderboard — revenue, on-time %, and rank (window functions)
WITH rep_stats AS (
    SELECT r.rep_name, r.region,
           COUNT(*) AS orders_handled,
           SUM(o.quantity * o.unit_price) AS revenue,
           AVG(CASE WHEN o.status = 'Shipped' AND o.ship_date <= o.promised_date THEN 1.0 ELSE 0 END) AS on_time_rate
    FROM orders o
    JOIN reps r ON r.rep_id = o.rep_id
    WHERE o.status = 'Shipped'
    GROUP BY r.rep_id
)
SELECT rep_name, region, orders_handled,
       ROUND(revenue, 2) AS revenue,
       ROUND(on_time_rate * 100, 1) AS on_time_pct,
       RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
       RANK() OVER (ORDER BY on_time_rate DESC) AS reliability_rank
FROM rep_stats
ORDER BY revenue_rank;

-- Q3: Monthly late-shipment trend (CTE + running total)
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           COUNT(*) AS total_orders,
           SUM(CASE WHEN status = 'Shipped' AND ship_date > promised_date THEN 1 ELSE 0 END) AS late_orders
    FROM orders
    GROUP BY 1
)
SELECT month, total_orders, late_orders,
       ROUND(late_orders * 100.0 / total_orders, 1) AS late_pct,
       SUM(late_orders) OVER (ORDER BY month) AS running_late_total
FROM monthly
ORDER BY month;

-- Q4: Open backlog — oldest unshipped orders and their value at risk
SELECT o.order_id, c.customer_name, c.region, r.rep_name,
       o.order_date, o.promised_date,
       CAST(julianday('2026-09-25') - julianday(o.order_date) AS INT) AS days_open,
       ROUND(o.quantity * o.unit_price, 2) AS order_value
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN reps r ON r.rep_id = o.rep_id
WHERE o.status = 'Open'
ORDER BY days_open DESC
LIMIT 15;

-- Q5: Cancellation rate by customer segment
SELECT c.segment,
       COUNT(*) AS total_orders,
       SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
       ROUND(SUM(CASE WHEN o.status = 'Cancelled' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) AS cancel_pct
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.segment
ORDER BY cancel_pct DESC;
