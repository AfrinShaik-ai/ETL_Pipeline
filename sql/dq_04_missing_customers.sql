
SELECT COUNT(*) AS failed_rows
FROM stg_orders AS o
LEFT JOIN stg_customers AS c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
