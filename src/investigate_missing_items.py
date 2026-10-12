
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    print("\n1. PAYMENT-BUT-NO-ITEMS BY ORDER STATUS")

    print(con.execute("""
        SELECT
            o.order_status,
            COUNT(DISTINCT p.order_id) AS orders
        FROM stg_payments p
        LEFT JOIN stg_order_items i
            ON p.order_id = i.order_id
        LEFT JOIN stg_orders o
            ON p.order_id = o.order_id
        WHERE i.order_id IS NULL
        GROUP BY o.order_status
        ORDER BY orders DESC
    """).df().to_string(index=False))

    print("\n2. SAMPLE OF PAYMENT-BUT-NO-ITEMS ORDERS")

    print(con.execute("""
        SELECT
            p.order_id,
            o.order_status,
            SUM(p.payment_value) AS payment_total,
            COUNT(*) AS payment_records
        FROM stg_payments p
        LEFT JOIN stg_order_items i
            ON p.order_id = i.order_id
        LEFT JOIN stg_orders o
            ON p.order_id = o.order_id
        WHERE i.order_id IS NULL
        GROUP BY p.order_id, o.order_status
        ORDER BY payment_total DESC
        LIMIT 15
    """).df().to_string(index=False))

    print("\n3. ORDER STATUS OF THE ORDER WITH ITEMS BUT NO PAYMENT")

    print(con.execute("""
        SELECT
            o.order_id,
            o.order_status,
            COUNT(i.order_item_id) AS item_count,
            SUM(i.price + i.freight_value) AS item_and_freight_total
        FROM stg_order_items i
        LEFT JOIN stg_payments p
            ON i.order_id = p.order_id
        LEFT JOIN stg_orders o
            ON i.order_id = o.order_id
        WHERE p.order_id IS NULL
        GROUP BY o.order_id, o.order_status
    """).df().to_string(index=False))
