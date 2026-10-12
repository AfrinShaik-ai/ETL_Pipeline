
SELECT COUNT(*) AS failed_rows
FROM (
    SELECT order_id
    FROM stg_orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) AS duplicates;
