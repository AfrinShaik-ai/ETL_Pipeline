
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    query = """
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
    ),
    mismatches AS (
        SELECT
            i.order_id,
            i.expected_total,
            p.paid_total,
            i.expected_total - p.paid_total AS difference
        FROM item_totals i
        JOIN payment_totals p
            ON i.order_id = p.order_id
        WHERE ABS(i.expected_total - p.paid_total) > 0.05
    )
    SELECT
        COALESCE(o.order_status, 'missing_order_record') AS order_status,
        COUNT(*) AS mismatched_orders,
        ROUND(SUM(ABS(m.difference)), 2) AS total_absolute_difference,
        ROUND(AVG(ABS(m.difference)), 2) AS average_absolute_difference
    FROM mismatches m
    LEFT JOIN stg_orders o
        ON m.order_id = o.order_id
    GROUP BY COALESCE(o.order_status, 'missing_order_record')
    ORDER BY mismatched_orders DESC;
    """

    print("PAYMENT MISMATCHES BY ORDER STATUS")
    print(con.execute(query).df().to_string(index=False))
