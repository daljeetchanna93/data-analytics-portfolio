-- =====================================================================
-- Olist E-Commerce Performance Analysis — SQL queries
-- Engine: SQLite 3.25+ (window functions). Tables are loaded from data/*.csv
-- by notebooks/ecommerce_sql_analysis.ipynb (see build_database()).
-- Each query starts with "-- name: <query_name>" so the notebook can run it.
-- Analysis window: Jan 2017 – Aug 2018 (complete months only).
-- =====================================================================


-- name: data_quality_overview
-- Row counts, date coverage and how many orders were actually delivered.
SELECT
    COUNT(*)                                                    AS total_orders,
    SUM(order_status = 'delivered')                             AS delivered_orders,
    ROUND(100.0 * SUM(order_status = 'delivered') / COUNT(*), 1) AS pct_delivered,
    SUM(order_status = 'canceled')                              AS canceled_orders,
    MIN(DATE(order_purchase_timestamp))                         AS first_order,
    MAX(DATE(order_purchase_timestamp))                         AS last_order,
    SUM(order_delivered_customer_date IS NULL
        AND order_status = 'delivered')                         AS delivered_missing_date
FROM orders;


-- name: monthly_revenue_growth
-- Monthly revenue, orders, AOV and month-over-month growth (LAG window function).
WITH order_revenue AS (
    SELECT o.order_id,
           STRFTIME('%Y-%m', o.order_purchase_timestamp) AS month,
           SUM(oi.price + oi.freight_value)              AS order_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-09-01'
    GROUP BY o.order_id, month
),
monthly AS (
    SELECT month,
           COUNT(*)                   AS orders,
           ROUND(SUM(order_value), 2) AS revenue,
           ROUND(AVG(order_value), 2) AS avg_order_value
    FROM order_revenue
    GROUP BY month
)
SELECT month,
       orders,
       revenue,
       avg_order_value,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1)            AS revenue_mom_pct,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2)              AS cumulative_revenue
FROM monthly
ORDER BY month;


-- name: top_categories
-- Top 10 product categories by revenue with share of total (window SUM) and rank.
WITH cat AS (
    SELECT COALESCE(t.product_category_name_english, 'unknown') AS category,
           COUNT(DISTINCT oi.order_id)                          AS orders,
           SUM(oi.price)                                        AS revenue,
           AVG(oi.price)                                        AS avg_item_price
    FROM order_items oi
    JOIN orders   o ON o.order_id   = oi.order_id AND o.order_status = 'delivered'
    JOIN products p ON p.product_id = oi.product_id
    LEFT JOIN product_category_name_translation t
           ON t.product_category_name = p.product_category_name
    GROUP BY category
)
SELECT RANK() OVER (ORDER BY revenue DESC)                     AS rank,
       category,
       orders,
       ROUND(revenue, 0)                                       AS revenue,
       ROUND(avg_item_price, 2)                                AS avg_item_price,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1)        AS pct_of_revenue,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
             / SUM(revenue) OVER (), 1)                        AS cumulative_pct
FROM cat
ORDER BY revenue DESC
LIMIT 10;


-- name: customer_repeat_rate
-- Share of unique customers (customer_unique_id) who placed 2+ orders.
WITH per_customer AS (
    SELECT c.customer_unique_id,
           COUNT(DISTINCT o.order_id) AS n_orders
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*)                                          AS customers,
       SUM(n_orders >= 2)                                AS repeat_customers,
       ROUND(100.0 * SUM(n_orders >= 2) / COUNT(*), 2)   AS repeat_rate_pct,
       ROUND(AVG(n_orders), 3)                           AS avg_orders_per_customer,
       MAX(n_orders)                                     AS max_orders_one_customer
FROM per_customer;


-- name: delivery_vs_reviews
-- Does late delivery hurt satisfaction? Compare review scores by delivery outcome.
WITH delivered AS (
    SELECT o.order_id,
           JULIANDAY(o.order_delivered_customer_date)
             - JULIANDAY(o.order_purchase_timestamp)       AS days_to_deliver,
           JULIANDAY(o.order_delivered_customer_date)
             - JULIANDAY(o.order_estimated_delivery_date)  AS days_vs_estimate
    FROM orders o
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
),
reviews AS (   -- one score per order (latest review if several)
    SELECT order_id, review_score
    FROM (SELECT order_id, review_score,
                 ROW_NUMBER() OVER (PARTITION BY order_id
                                    ORDER BY review_creation_date DESC) AS rn
          FROM order_reviews)
    WHERE rn = 1
)
SELECT CASE
         WHEN d.days_vs_estimate <= 0  THEN '1. On time / early'
         WHEN d.days_vs_estimate <= 3  THEN '2. Late 1-3 days'
         WHEN d.days_vs_estimate <= 7  THEN '3. Late 4-7 days'
         ELSE                               '4. Late 8+ days'
       END                                               AS delivery_bucket,
       COUNT(*)                                          AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_orders,
       ROUND(AVG(d.days_to_deliver), 1)                  AS avg_days_to_deliver,
       ROUND(AVG(r.review_score), 2)                     AS avg_review_score,
       ROUND(100.0 * AVG(r.review_score = 1), 1)         AS pct_one_star
FROM delivered d
JOIN reviews r ON r.order_id = d.order_id
GROUP BY delivery_bucket
ORDER BY delivery_bucket;


-- name: state_performance
-- Revenue, delivery speed and late-delivery rate by customer state (top 10 by revenue).
-- Items are rolled up to one row per order first so each order counts once.
WITH order_level AS (
    SELECT o.order_id,
           c.customer_state,
           SUM(oi.price + oi.freight_value)                  AS order_value,
           SUM(oi.freight_value) / NULLIF(SUM(oi.price), 0)  AS freight_ratio,
           JULIANDAY(o.order_delivered_customer_date)
             - JULIANDAY(o.order_purchase_timestamp)         AS days_to_deliver,
           o.order_delivered_customer_date
             > o.order_estimated_delivery_date               AS is_late
    FROM orders o
    JOIN customers   c  ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id   = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY o.order_id, c.customer_state
)
SELECT customer_state                        AS state,
       COUNT(*)                              AS orders,
       ROUND(SUM(order_value), 0)            AS revenue,
       ROUND(100.0 * AVG(freight_ratio), 1)  AS freight_pct_of_price,
       ROUND(AVG(days_to_deliver), 1)        AS avg_days_to_deliver,
       ROUND(100.0 * AVG(is_late), 1)        AS late_pct
FROM order_level
GROUP BY customer_state
ORDER BY revenue DESC
LIMIT 10;


-- name: seller_concentration
-- How concentrated is revenue among sellers? NTILE(10) splits sellers into deciles.
WITH seller_rev AS (
    SELECT oi.seller_id, SUM(oi.price) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id AND o.order_status = 'delivered'
    GROUP BY oi.seller_id
),
ranked AS (
    SELECT seller_id, revenue,
           NTILE(10) OVER (ORDER BY revenue DESC) AS decile
    FROM seller_rev
)
SELECT decile,
       COUNT(*)                                             AS sellers,
       ROUND(SUM(revenue), 0)                               AS revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM seller_rev), 1) AS pct_of_revenue
FROM ranked
GROUP BY decile
ORDER BY decile;


-- name: payment_mix
-- Payment methods: share of orders and average installments.
SELECT payment_type,
       COUNT(DISTINCT order_id)                                   AS orders,
       ROUND(100.0 * COUNT(DISTINCT order_id)
             / (SELECT COUNT(DISTINCT order_id) FROM order_payments), 1) AS pct_of_orders,
       ROUND(AVG(payment_value), 2)                               AS avg_payment,
       ROUND(AVG(payment_installments), 1)                        AS avg_installments
FROM order_payments
WHERE payment_type <> 'not_defined'
GROUP BY payment_type
ORDER BY orders DESC;
