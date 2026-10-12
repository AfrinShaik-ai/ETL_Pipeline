
from pathlib import Path
import duckdb
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"
REPORTS_DIR = PROJECT_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: reports/{filename}")


with duckdb.connect(str(DB_PATH), read_only=True) as con:

    # Chart 1: Monthly revenue
    rows = con.execute("""
        SELECT
            DATE_TRUNC('month', purchase_ts)::DATE AS month_start,
            SUM(item_revenue) AS revenue
        FROM mart_orders
        WHERE order_status = 'delivered'
          AND purchase_ts IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).fetchall()

    dates = [r[0] for r in rows]
    revenue = [float(r[1]) for r in rows]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, revenue, marker="o")
    plt.title("Monthly Revenue from Delivered Orders")
    plt.xlabel("Month")
    plt.ylabel("Revenue (dataset monetary units)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    save_chart("chart_01_monthly_revenue.png")

    # Chart 2: Top 10 product categories by item revenue
    rows = con.execute("""
        SELECT
            COALESCE(
                ct.category_english,
                p.product_category_name,
                'unknown'
            ) AS category_name,
            SUM(i.price) AS revenue
        FROM stg_order_items i
        JOIN stg_orders o ON i.order_id = o.order_id
        JOIN stg_products p ON i.product_id = p.product_id
        LEFT JOIN stg_category_translation ct
            ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY 1
        ORDER BY revenue DESC
        LIMIT 10
    """).fetchall()

    categories = [r[0] for r in rows][::-1]
    category_revenue = [float(r[1]) for r in rows][::-1]

    plt.figure(figsize=(10, 6))
    plt.barh(categories, category_revenue)
    plt.title("Top 10 Product Categories by Revenue")
    plt.xlabel("Item revenue (dataset monetary units)")
    plt.ylabel("Product category")
    save_chart("chart_02_top_categories.png")

    # Chart 3: Daily orders and seven-day rolling average
    rows = con.execute("""
        WITH daily AS (
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
                (SELECT MIN(order_date) FROM daily),
                (SELECT MAX(order_date) FROM daily),
                INTERVAL 1 DAY
            ) AS dates(day)
        ),
        series AS (
            SELECT
                c.order_date,
                COALESCE(d.order_count, 0) AS order_count
            FROM calendar c
            LEFT JOIN daily d USING (order_date)
        )
        SELECT
            order_date,
            order_count,
            AVG(order_count) OVER (
                ORDER BY order_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) AS rolling_average
        FROM series
        ORDER BY order_date
    """).fetchall()

    dates = [r[0] for r in rows]
    daily_counts = [int(r[1]) for r in rows]
    rolling_avg = [float(r[2]) for r in rows]

    plt.figure(figsize=(11, 5))
    plt.plot(dates, daily_counts, alpha=0.35, label="Daily orders")
    plt.plot(dates, rolling_avg, linewidth=2, label="7-day rolling average")
    plt.title("Daily Orders and Seven-Day Rolling Average")
    plt.xlabel("Date")
    plt.ylabel("Number of orders")
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_chart("chart_03_daily_orders.png")

    # Chart 4: Delivery performance by average review score
    rows = con.execute("""
        SELECT
            average_review_score,
            COUNT(*) AS reviewed_orders,
            AVG(delivery_delay_days) AS average_delay
        FROM mart_orders
        WHERE order_status = 'delivered'
          AND average_review_score IS NOT NULL
          AND delivery_delay_days IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).fetchall()

    scores = [str(r[0]) for r in rows]
    avg_delay = [float(r[2]) for r in rows]

    plt.figure(figsize=(9, 5))
    plt.bar(scores, avg_delay)
    plt.axhline(0, linewidth=1)
    plt.title("Average Delivery Delay by Average Review Score")
    plt.xlabel("Average review score")
    plt.ylabel("Average delay in days (negative = early)")
    plt.grid(axis="y", alpha=0.3)
    save_chart("chart_04_delivery_reviews.png")

print("\nAll four charts have been generated.")
