
WITH daily_orders AS (
    SELECT
        CAST(purchase_ts AS DATE) AS order_date,
        COUNT(*) AS order_count
    FROM mart_orders
    WHERE purchase_ts IS NOT NULL
    GROUP BY 1
),
calendar AS (
    SELECT CAST(day AS DATE) AS order_date
    FROM generate_series(
        (SELECT MIN(order_date) FROM daily_orders),
        (SELECT MAX(order_date) FROM daily_orders),
        INTERVAL 1 DAY
    ) AS dates(day)
),
daily_series AS (
    SELECT
        c.order_date,
        COALESCE(d.order_count, 0) AS order_count
    FROM calendar c
    LEFT JOIN daily_orders d
        ON c.order_date = d.order_date
)
SELECT
    order_date,
    order_count,
    ROUND(
        AVG(order_count) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_7_day_average
FROM daily_series
ORDER BY order_date;
