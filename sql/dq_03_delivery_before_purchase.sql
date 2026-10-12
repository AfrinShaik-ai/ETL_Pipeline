
SELECT COUNT(*) AS failed_rows
FROM stg_orders
WHERE delivered_ts < purchase_ts;
