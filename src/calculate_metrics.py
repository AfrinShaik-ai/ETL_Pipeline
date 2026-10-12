
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(DB_PATH), read_only=True) as con:

    print("\n1. LATE-DELIVERY METRICS")

    print(con.execute("""
        SELECT
            COUNT(*) AS eligible_delivered_orders,
            COUNT(*) FILTER (
                WHERE delivery_delay_days > 0
            ) AS late_orders,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE delivery_delay_days > 0
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS late_delivery_rate_percentage
        FROM mart_orders
        WHERE order_status = 'delivered'
          AND delivered_ts IS NOT NULL
          AND estimated_delivery_ts IS NOT NULL
          AND delivery_delay_days IS NOT NULL
    """).df().to_string(index=False))

    print("\n2. PAYMENT RECONCILIATION METRICS")

    print(con.execute("""
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
        comparable_orders AS (
            SELECT
                i.order_id,
                i.expected_total,
                p.paid_total
            FROM item_totals i
            JOIN payment_totals p
                ON i.order_id = p.order_id
        )
        SELECT
            COUNT(*) AS comparable_orders,
            COUNT(*) FILTER (
                WHERE ABS(expected_total - paid_total) > 0.05
            ) AS mismatched_orders,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE ABS(expected_total - paid_total) > 0.05
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS mismatch_rate_percentage
        FROM comparable_orders
    """).df().to_string(index=False))
