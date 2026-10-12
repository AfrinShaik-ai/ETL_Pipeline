
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    query = """
    WITH items AS (
        SELECT
            order_id,
            COUNT(*) AS item_count,
            SUM(price + freight_value) AS expected_total
        FROM stg_order_items
        GROUP BY order_id
    ),
    payments AS (
        SELECT
            order_id,
            COUNT(*) AS payment_records,
            SUM(payment_value) AS paid_total,
            STRING_AGG(DISTINCT payment_type, ', ') AS payment_methods
        FROM stg_payments
        GROUP BY order_id
    )
    SELECT
        o.order_id,
        i.item_count,
        i.expected_total,
        p.paid_total,
        ROUND(i.expected_total - p.paid_total, 2) AS difference,
        p.payment_records,
        p.payment_methods
    FROM stg_orders o
    JOIN items i ON o.order_id = i.order_id
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
      AND ABS(i.expected_total - p.paid_total) > 0.05
    ORDER BY ABS(i.expected_total - p.paid_total) DESC
    LIMIT 10
    """

    print("10 LARGEST DELIVERED-ORDER MISMATCHES")
    print(con.execute(query).df().to_string(index=False))
