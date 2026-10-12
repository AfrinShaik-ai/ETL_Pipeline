
from pathlib import Path
import csv
import logging

import duckdb


# --------------------------------------------------
# 1. Project paths and logging
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
DB_DIR = PROJECT_DIR / "data" / "processed"
DB_PATH = DB_DIR / "olist.duckdb"
LOG_DIR = PROJECT_DIR / "reports"
LOG_PATH = LOG_DIR / "pipeline.log"

DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
    force=True,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# 2. Source files and required columns
# --------------------------------------------------

FILES = {
    "orders": (
        "olist_orders_dataset.csv",
        [
            "order_id", "customer_id", "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    "order_items": (
        "olist_order_items_dataset.csv",
        [
            "order_id", "order_item_id", "product_id",
            "seller_id", "shipping_limit_date",
            "price", "freight_value",
        ],
    ),
    "payments": (
        "olist_order_payments_dataset.csv",
        [
            "order_id", "payment_sequential", "payment_type",
            "payment_installments", "payment_value",
        ],
    ),
    "reviews": (
        "olist_order_reviews_dataset.csv",
        ["review_id", "order_id", "review_score"],
    ),
    "customers": (
        "olist_customers_dataset.csv",
        [
            "customer_id", "customer_unique_id",
            "customer_city", "customer_state",
        ],
    ),
    "sellers": (
        "olist_sellers_dataset.csv",
        ["seller_id", "seller_city", "seller_state"],
    ),
    "products": (
        "olist_products_dataset.csv",
        ["product_id", "product_category_name"],
    ),
    "geolocation": (
        "olist_geolocation_dataset.csv",
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat", "geolocation_lng",
            "geolocation_city", "geolocation_state",
        ],
    ),
    "category_translation": (
        "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
    ),
}


def quote_identifier(name):
    """Safely quote a database identifier."""
    return '"' + name.replace('"', '""') + '"'


def quote_literal(value):
    """Safely quote a SQL string literal."""
    return "'" + str(value).replace("'", "''") + "'"


# --------------------------------------------------
# 3. Validate files and columns before loading
# --------------------------------------------------

def validate_sources():
    logger.info("Checking source files and required columns")

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data directory does not exist: {RAW_DIR}"
        )

    for table_name, (filename, required_columns) in FILES.items():
        file_path = RAW_DIR / filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Required source file is missing: {file_path}"
            )

        try:
            with file_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                headers = next(csv.reader(file), None)
        except Exception as exc:
            raise RuntimeError(
                f"Cannot read source file {filename}: {exc}"
            ) from exc

        if headers is None:
            raise ValueError(f"Source file is empty: {filename}")

        missing = set(required_columns) - set(headers)

        if missing:
            raise ValueError(
                f"{filename} is missing required columns: "
                f"{sorted(missing)}"
            )

        logger.info("Validated %s", filename)


# --------------------------------------------------
# 4. Load CSVs into raw database tables
# --------------------------------------------------

def load_raw_tables(con):
    logger.info("Loading raw source tables")

    for table_name, (filename, _) in FILES.items():
        file_path = RAW_DIR / filename

        sql = (
            f"CREATE OR REPLACE TABLE "
            f"{quote_identifier('raw_' + table_name)} AS "
            f"SELECT * FROM read_csv_auto("
            f"{quote_literal(file_path)}, "
            f"header=true, all_varchar=true)"
        )

        con.execute(sql)

        row_count = con.execute(
            f"SELECT COUNT(*) FROM "
            f"{quote_identifier('raw_' + table_name)}"
        ).fetchone()[0]

        logger.info(
            "Loaded raw_%s: %s rows",
            table_name,
            f"{row_count:,}",
        )


# --------------------------------------------------
# 5. Create cleaned staging tables
# --------------------------------------------------

def build_staging_tables(con):
    logger.info("Building staging tables")

    statements = [
        """
        CREATE OR REPLACE TABLE stg_orders AS
        SELECT
            NULLIF(TRIM(order_id), '') AS order_id,
            NULLIF(TRIM(customer_id), '') AS customer_id,
            NULLIF(TRIM(order_status), '') AS order_status,
            TRY_CAST(NULLIF(TRIM(order_purchase_timestamp), '')
                AS TIMESTAMP) AS purchase_ts,
            TRY_CAST(NULLIF(TRIM(order_approved_at), '')
                AS TIMESTAMP) AS approved_ts,
            TRY_CAST(NULLIF(TRIM(order_delivered_carrier_date), '')
                AS TIMESTAMP) AS carrier_delivery_ts,
            TRY_CAST(NULLIF(TRIM(order_delivered_customer_date), '')
                AS TIMESTAMP) AS delivered_ts,
            TRY_CAST(NULLIF(TRIM(order_estimated_delivery_date), '')
                AS TIMESTAMP) AS estimated_delivery_ts
        FROM raw_orders
        """,
        """
        CREATE OR REPLACE TABLE stg_customers AS
        SELECT
            NULLIF(TRIM(customer_id), '') AS customer_id,
            NULLIF(TRIM(customer_unique_id), '') AS customer_unique_id,
            TRIM(customer_city) AS customer_city,
            TRIM(customer_state) AS customer_state
        FROM raw_customers
        """,
        """
        CREATE OR REPLACE TABLE stg_order_items AS
        SELECT
            NULLIF(TRIM(order_id), '') AS order_id,
            TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
            NULLIF(TRIM(product_id), '') AS product_id,
            NULLIF(TRIM(seller_id), '') AS seller_id,
            TRY_CAST(price AS DECIMAL(12, 2)) AS price,
            TRY_CAST(freight_value AS DECIMAL(12, 2))
                AS freight_value
        FROM raw_order_items
        """,
        """
        CREATE OR REPLACE TABLE stg_payments AS
        SELECT
            NULLIF(TRIM(order_id), '') AS order_id,
            TRY_CAST(payment_sequential AS INTEGER)
                AS payment_sequential,
            NULLIF(TRIM(payment_type), '') AS payment_type,
            TRY_CAST(payment_installments AS INTEGER)
                AS payment_installments,
            TRY_CAST(payment_value AS DECIMAL(12, 2))
                AS payment_value
        FROM raw_payments
        """,
        """
        CREATE OR REPLACE TABLE stg_reviews AS
        SELECT
            NULLIF(TRIM(review_id), '') AS review_id,
            NULLIF(TRIM(order_id), '') AS order_id,
            TRY_CAST(review_score AS INTEGER) AS review_score
        FROM raw_reviews
        """,
        """
        CREATE OR REPLACE TABLE stg_products AS
        SELECT
            NULLIF(TRIM(product_id), '') AS product_id,
            NULLIF(TRIM(product_category_name), '')
                AS product_category_name
        FROM raw_products
        """,
        """
        CREATE OR REPLACE TABLE stg_sellers AS
        SELECT
            NULLIF(TRIM(seller_id), '') AS seller_id,
            TRIM(seller_city) AS seller_city,
            TRIM(seller_state) AS seller_state
        FROM raw_sellers
        """,
        """
        CREATE OR REPLACE TABLE stg_geolocation AS
        SELECT
            TRY_CAST(geolocation_zip_code_prefix AS INTEGER)
                AS zip_code_prefix,
            TRY_CAST(geolocation_lat AS DOUBLE) AS latitude,
            TRY_CAST(geolocation_lng AS DOUBLE) AS longitude,
            TRIM(geolocation_city) AS city,
            TRIM(geolocation_state) AS state
        FROM raw_geolocation
        """,
        """
        CREATE OR REPLACE TABLE stg_category_translation AS
        SELECT
            NULLIF(TRIM(product_category_name), '')
                AS product_category_name,
            NULLIF(TRIM(product_category_name_english), '')
                AS category_english
        FROM raw_category_translation
        """,
    ]

    for statement in statements:
        con.execute(statement)
        table_name = statement.split("TABLE ", 1)[1].split()[0]

        count = con.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(table_name)}"
        ).fetchone()[0]

        logger.info("Built %s: %s rows", table_name, f"{count:,}")


# --------------------------------------------------
# 6. Build an order-level analysis mart
# --------------------------------------------------

def build_mart(con):
    logger.info("Building mart_orders")

    con.execute("""
        CREATE OR REPLACE TABLE mart_orders AS
        WITH item_totals AS (
            SELECT
                order_id,
                SUM(price) AS item_revenue,
                SUM(freight_value) AS freight_total,
                COUNT(*) AS item_count
            FROM stg_order_items
            GROUP BY order_id
        ),
        payment_totals AS (
            SELECT
                order_id,
                SUM(payment_value) AS payment_total
            FROM stg_payments
            GROUP BY order_id
        ),
        review_totals AS (
            SELECT
                order_id,
                AVG(review_score) AS average_review_score,
                COUNT(review_score) AS review_count
            FROM stg_reviews
            GROUP BY order_id
        )
        SELECT
            o.order_id,
            o.customer_id,
            c.customer_unique_id,
            c.customer_state,
            o.order_status,
            o.purchase_ts,
            o.approved_ts,
            o.carrier_delivery_ts,
            o.delivered_ts,
            o.estimated_delivery_ts,
            i.item_revenue,
            i.freight_total,
            COALESCE(i.item_count, 0) AS item_count,
            p.payment_total,
            r.average_review_score,
            COALESCE(r.review_count, 0) AS review_count,
            CASE
                WHEN o.delivered_ts IS NOT NULL
                 AND o.estimated_delivery_ts IS NOT NULL
                THEN DATE_DIFF(
                    'day',
                    CAST(o.estimated_delivery_ts AS DATE),
                    CAST(o.delivered_ts AS DATE)
                )
                ELSE NULL
            END AS delivery_delay_days
        FROM stg_orders o
        LEFT JOIN stg_customers c
            ON o.customer_id = c.customer_id
        LEFT JOIN item_totals i
            ON o.order_id = i.order_id
        LEFT JOIN payment_totals p
            ON o.order_id = p.order_id
        LEFT JOIN review_totals r
            ON o.order_id = r.order_id
    """)

    row_count = con.execute(
        "SELECT COUNT(*) FROM mart_orders"
    ).fetchone()[0]

    unique_count = con.execute(
        "SELECT COUNT(DISTINCT order_id) FROM mart_orders"
    ).fetchone()[0]

    logger.info(
        "Built mart_orders with %s rows",
        f"{row_count:,}",
    )

    if row_count != unique_count:
        raise RuntimeError(
            "Mart grain violation: duplicate or null order IDs detected"
        )


# --------------------------------------------------
# 7. Critical data-quality alarms
# --------------------------------------------------


def run_critical_checks(con):
    """Execute every SQL quality check and stop on failures."""
    logger.info("Running SQL data-quality checks")

    sql_dir = PROJECT_DIR / "sql"
    check_files = sorted(sql_dir.glob("dq_*.sql"))

    if len(check_files) < 5:
        raise RuntimeError(
            f"Expected at least 5 SQL checks in {sql_dir}; "
            f"found {len(check_files)}"
        )

    failures = []

    for check_file in check_files:
        try:
            query = check_file.read_text(encoding="utf-8")
            result = con.execute(query).fetchone()

            if result is None:
                raise ValueError("Query returned no result")

            failed_rows = result[0]

            if not isinstance(failed_rows, int):
                failed_rows = int(failed_rows)

            if failed_rows < 0:
                raise ValueError("Failure count cannot be negative")

            logger.info(
                "Check: %s | failing rows/groups: %s",
                check_file.name,
                f"{failed_rows:,}",
            )

            if failed_rows > 0:
                failures.append(
                    f"{check_file.name}: {failed_rows} failures"
                )

        except Exception as exc:
            logger.exception(
                "Could not execute check %s",
                check_file.name,
            )
            raise RuntimeError(
                f"Quality check could not run: "
                f"{check_file.name}: {exc}"
            ) from exc

    if failures:
        raise RuntimeError(
            "DATA QUALITY ALARM: " + "; ".join(failures)
        )

    logger.info(
        "All %s SQL data-quality checks passed",
        len(check_files),
    )



# --------------------------------------------------
# 8. Pipeline entry point
# --------------------------------------------------

def main():
    logger.info("========== PIPELINE STARTED ==========")

    # Validate before modifying database tables.
    validate_sources()

    try:
        with duckdb.connect(str(DB_PATH)) as con:
            load_raw_tables(con)
            build_staging_tables(con)
            build_mart(con)
            run_critical_checks(con)

        logger.info("========== PIPELINE SUCCEEDED ==========")
        logger.info("Database saved at: %s", DB_PATH)

    except Exception:
        logger.exception("PIPELINE FAILED")
        raise


if __name__ == "__main__":
    main()
