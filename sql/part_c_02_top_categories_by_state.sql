
WITH category_revenue AS (
    SELECT
        m.customer_state,
        COALESCE(
            ct.category_english,
            p.product_category_name,
            'unknown'
        ) AS category_name,
        SUM(i.price) AS revenue
    FROM mart_orders m
    JOIN stg_order_items i
        ON m.order_id = i.order_id
    JOIN stg_products p
        ON i.product_id = p.product_id
    LEFT JOIN stg_category_translation ct
        ON p.product_category_name =
           ct.product_category_name
    WHERE m.order_status = 'delivered'
      AND m.customer_state IS NOT NULL
    GROUP BY 1, 2
),
ranked_categories AS (
    SELECT
        customer_state,
        category_name,
        revenue,
        DENSE_RANK() OVER (
            PARTITION BY customer_state
            ORDER BY revenue DESC
        ) AS category_rank
    FROM category_revenue
)
SELECT
    customer_state,
    category_name,
    ROUND(revenue, 2) AS revenue,
    category_rank
FROM ranked_categories
WHERE category_rank <= 3
ORDER BY customer_state, category_rank, category_name;
