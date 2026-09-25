-- ============================================================================
-- RFM Customer Segmentation
-- Computes Recency / Frequency / Monetary per customer, scores each dimension
-- 1-5 with NTILE quintiles, and assigns every customer to one segment.
--
-- Run:  sqlite3 data/customers.db < rfm_analysis.sql
--
-- Portable SQL: CTEs + window functions (NTILE) work in Postgres, SQL Server,
-- Snowflake, and BigQuery. A fixed "as of" date keeps results reproducible.
-- ============================================================================

DROP VIEW IF EXISTS customer_rfm;

CREATE VIEW customer_rfm AS
WITH params AS (
    -- Fixed analysis date: recency is measured against this, never "today".
    SELECT DATE('2026-09-30') AS as_of
),
base AS (
    SELECT
        c.customer_id,
        c.name,
        c.region,
        CAST(julianday((SELECT as_of FROM params))
             - julianday(MAX(t.txn_date)) AS INTEGER) AS recency_days,
        COUNT(*)                                       AS frequency,
        ROUND(SUM(t.amount), 2)                        AS monetary
    FROM customers c
    JOIN transactions t ON t.customer_id = c.customer_id
    GROUP BY c.customer_id, c.name, c.region
),
scored AS (
    SELECT
        *,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,  -- 5 = most recent
        NTILE(5) OVER (ORDER BY frequency ASC)        AS f_score,  -- 5 = most frequent
        NTILE(5) OVER (ORDER BY monetary ASC)         AS m_score   -- 5 = highest spend
    FROM base
),
segmented AS (
    SELECT
        *,
        (r_score || f_score || m_score) AS rfm_code,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
            WHEN r_score = 3  AND f_score >= 4 THEN 'Loyal Customers'
            WHEN r_score <= 2 AND f_score >= 4 THEN 'Can''t Lose Them'
            WHEN r_score <= 2 AND f_score = 3  THEN 'At Risk'
            WHEN r_score = 5  AND f_score <= 2 THEN 'New Customers'
            WHEN r_score >= 4 AND f_score <= 3 THEN 'Potential Loyalists'
            WHEN r_score = 3  AND f_score <= 3 THEN 'Need Attention'
            WHEN r_score = 2  AND f_score <= 2 THEN 'Hibernating'
            WHEN r_score = 1  AND f_score <= 2 THEN 'Lost'
        END AS segment
    FROM scored
)
SELECT * FROM segmented;

-- ----------------------------------------------------------------------------
-- Segment summary: size, revenue concentration, and behavior per segment.
-- ----------------------------------------------------------------------------
SELECT
    segment,
    COUNT(*)                                                    AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)           AS pct_of_customers,
    ROUND(SUM(monetary), 0)                                     AS total_revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(monetary), 0)                                     AS avg_monetary,
    ROUND(AVG(recency_days), 0)                                 AS avg_recency_days,
    ROUND(AVG(frequency), 1)                                    AS avg_frequency
FROM customer_rfm
GROUP BY segment
ORDER BY total_revenue DESC;
