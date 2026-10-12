
SELECT
    average_review_score AS review_score,
    COUNT(*) AS reviewed_orders,
    ROUND(AVG(delivery_delay_days), 2) AS average_delay_days,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE delivery_delay_days > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS late_delivery_percentage
FROM mart_orders
WHERE order_status = 'delivered'
  AND average_review_score IS NOT NULL
  AND delivered_ts IS NOT NULL
  AND estimated_delivery_ts IS NOT NULL
  AND delivery_delay_days IS NOT NULL
GROUP BY average_review_score
ORDER BY review_score;
