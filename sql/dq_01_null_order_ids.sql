SELECT COUNT(*) AS failed_rows
FROM stg_orders
WHERE order_id IS NULL;
