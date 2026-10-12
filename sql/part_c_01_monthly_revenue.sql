
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', purchase_ts)::DATE AS month_start,
        SUM(item_revenue) AS revenue
    FROM mart_orders
    WHERE order_status = 'delivered'
      AND purchase_ts IS NOT NULL
    GROUP BY 1
),
month_calendar AS (
    SELECT CAST(month AS DATE) AS month_start
    FROM generate_series(
        (SELECT MIN(month_start) FROM monthly_revenue),
        (SELECT MAX(month_start) FROM monthly_revenue),
        INTERVAL 1 MONTH
    ) AS months(month)
),
complete_months AS (
    SELECT
        c.month_start,
        COALESCE(r.revenue, 0) AS revenue
    FROM month_calendar c
    LEFT JOIN monthly_revenue r
        ON c.month_start = r.month_start
),
revenue_with_previous AS (
    SELECT
        month_start,
        revenue,
        LAG(revenue) OVER (
            ORDER BY month_start
        ) AS previous_month_revenue
    FROM complete_months
)
SELECT
    month_start,
    ROUND(revenue, 2) AS revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(
        100.0 * (revenue - previous_month_revenue)
        / NULLIF(previous_month_revenue, 0),
        2
    ) AS growth_percentage
FROM revenue_with_previous
ORDER BY month_start;
