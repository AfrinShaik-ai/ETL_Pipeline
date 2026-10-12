
WITH item_totals AS (
    SELECT
        order_id,
        SUM(price + freight_value) AS expected_total
    FROM stg_order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS paid_total
    FROM stg_payments
    GROUP BY order_id
)
SELECT COUNT(*) AS failed_rows
FROM item_totals AS i
JOIN payment_totals AS p
    ON i.order_id = p.order_id
WHERE ABS(i.expected_total - p.paid_total) > 0.05;
