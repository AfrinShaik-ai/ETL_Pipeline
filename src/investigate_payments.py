
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(DB_PATH), read_only=True) as con:

    # Compare aggregated item and payment totals.
    con.execute("""
        CREATE OR REPLACE TEMP VIEW payment_differences AS
        WITH items AS (
            SELECT
                order_id,
                SUM(price + freight_value) AS expected_total
            FROM stg_order_items
            GROUP BY order_id
        ),
        payments AS (
            SELECT
                order_id,
                SUM(payment_value) AS paid_total
            FROM stg_payments
            GROUP BY order_id
        )
        SELECT
            i.order_id,
            i.expected_total,
            p.paid_total,
            ROUND(
                i.expected_total - p.paid_total, 2
            ) AS difference
        FROM items i
        JOIN payments p USING (order_id)
        WHERE ABS(i.expected_total - p.paid_total) > 0.05
    """)

    print("\n1. MISMATCH SUMMARY")
    print(con.execute("""
        SELECT
            COUNT(*) AS mismatched_orders,
            ROUND(SUM(ABS(difference)), 2)
                AS total_absolute_difference,
            ROUND(AVG(ABS(difference)), 2)
                AS average_absolute_difference,
            ROUND(MAX(ABS(difference)), 2)
                AS largest_absolute_difference
        FROM payment_differences
    """).df().to_string(index=False))

    print("\n2. FIRST 20 MISMATCHED ORDERS")
    print(con.execute("""
        SELECT *
        FROM payment_differences
        ORDER BY ABS(difference) DESC
        LIMIT 20
    """).df().to_string(index=False))

    print("\n3. MISMATCH SIZE DISTRIBUTION")
    print(con.execute("""
        SELECT
            CASE
                WHEN ABS(difference) <= 1
                    THEN '0.05 to 1'
                WHEN ABS(difference) <= 10
                    THEN '1 to 10'
                WHEN ABS(difference) <= 100
                    THEN '10 to 100'
                ELSE 'Above 100'
            END AS difference_range,
            COUNT(*) AS orders
        FROM payment_differences
        GROUP BY 1
        ORDER BY 1
    """).df().to_string(index=False))

    print("\n4. PAYMENT METHODS ON MISMATCHED ORDERS")
    print(con.execute("""
        WITH bad_orders AS (
            SELECT order_id FROM payment_differences
        )
        SELECT
            p.payment_type,
            COUNT(DISTINCT p.order_id) AS affected_orders,
            ROUND(SUM(p.payment_value), 2) AS payment_total
        FROM stg_payments p
        JOIN bad_orders b USING (order_id)
        GROUP BY p.payment_type
        ORDER BY affected_orders DESC
    """).df().to_string(index=False))

    print("\n5. ORDERS WITH ITEMS BUT NO PAYMENT")
    print(con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT i.order_id
            FROM stg_order_items i
            LEFT JOIN stg_payments p USING (order_id)
            WHERE p.order_id IS NULL
        ) missing
    """).fetchall()[0][0])

    print("\n6. ORDERS WITH PAYMENT BUT NO ITEMS")
    print(con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT p.order_id
            FROM stg_payments p
            LEFT JOIN stg_order_items i USING (order_id)
            WHERE i.order_id IS NULL
        ) missing
    """).fetchall()[0][0])
