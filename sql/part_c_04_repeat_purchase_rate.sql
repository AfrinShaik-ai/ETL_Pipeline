
WITH customer_orders AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS order_count
    FROM mart_orders
    WHERE customer_unique_id IS NOT NULL
      AND order_status = 'delivered'
    GROUP BY customer_unique_id
)
SELECT
    COUNT(*) AS unique_customers,
    COUNT(*) FILTER (
        WHERE order_count >= 2
    ) AS repeat_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_count >= 2
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_purchase_rate_percentage
FROM customer_orders;
