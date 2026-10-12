# BDA Take-Home Assignment 1
## E-commerce Data Engineering and Analytics

### 1. Project Overview

This project implements a Python-based ELT (Extract, Load, Transform) pipeline for the Olist e-commerce dataset. It loads raw CSV files into DuckDB, creates cleaned staging tables, builds an order-level analytical data mart, executes SQL-based data-quality checks, and performs business analysis using SQL.

The project also includes business metrics, visualizations, and a short executive memo.

### 2. Technologies Used

- **Python:** Pipeline orchestration and metric calculations
- **DuckDB:** Data storage, transformation, validation, and SQL analytics
- **SQL:** Data-quality checks and business analysis
- **Pandas:** Supporting data handling
- **Matplotlib:** Data visualization

### 3. Project Structure

```text
BDA_Assignment/
├── data/
│   ├── raw/                 # Original CSV files
│   └── processed/           # Generated database and processed data
├── src/
│   ├── pipeline.py          # ELT pipeline
│   ├── run_part_c.py        # Executes Part C SQL queries
│   ├── calculate_metrics.py # Calculates supporting metrics
│   └── make_charts.py       # Generates charts
├── sql/
│   ├── dq_01_null_order_ids.sql
│   ├── dq_02_duplicate_order_ids.sql
│   ├── dq_03_delivery_before_purchase.sql
│   ├── dq_04_missing_customers.sql
│   ├── dq_05_payment_mismatch.sql
│   ├── dq_06_invalid_review_scores.sql
│   ├── part_c_01_monthly_revenue.sql
│   ├── part_c_02_top_categories_by_state.sql
│   ├── part_c_03_rolling_7_day_orders.sql
│   ├── part_c_04_repeat_purchase_rate.sql
│   └── part_c_05_delivery_delay_reviews.sql
├── reports/
│   ├── chart_01_monthly_revenue.png
│   ├── chart_02_top_categories.png
│   ├── chart_03_daily_orders.png
│   ├── chart_04_delivery_reviews.png
│   └── vp_memo.md
├── requirements.txt
└── README.md
```

### 4. Dataset

The project uses the Olist Brazilian e-commerce dataset. The raw CSV files must be placed in `data/raw/` before running the pipeline.

The pipeline checks that the required source files and columns are available before processing the data.

### 5. Installation and Setup

Install Python, then open PowerShell in the project directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 6. Running the Project

**Step 1 — Run the ELT pipeline**

```powershell
python src\pipeline.py
```

The pipeline loads the raw CSV files, creates staging tables and the analytical mart, and runs the data-quality checks.

**Important:** The current dataset produces 260 payment-reconciliation mismatches. The pipeline therefore stops when this check fails. This is intentional fail-fast behavior, and the issue should be investigated rather than silently ignored.

**Step 2 — Execute the Part C SQL queries**

```powershell
python src\run_part_c.py
```

This executes the five SQL analysis files and displays their results.

**Step 3 — Calculate supporting metrics**

```powershell
python src\calculate_metrics.py
```

**Step 4 — Generate the visualizations**

```powershell
python src\make_charts.py
```

Run the metric and chart scripts after the pipeline has created the database and analytical tables. If the pipeline stops after creating the tables, verify that the required tables are available before running the other scripts.

### 7. Data-Quality Checks

The project includes checks for:

1. Null order IDs
2. Duplicate order IDs
3. Delivery timestamps earlier than purchase timestamps
4. Orders without matching customers
5. Payment totals that differ from item-plus-freight totals by more than 0.05
6. Invalid or missing review scores

The current results show zero failures for checks 1, 2, 3, 4, and 6. Check 5 identifies 260 mismatched orders.

Additional investigation identified 775 orders with payment records but no matching order items and one order with items but no payment record. These findings are documented for further investigation.

### 8. Business Analysis

The five SQL queries analyse:

- Monthly delivered-item revenue and month-over-month growth
- Top three product categories by customer state
- Seven-day rolling average of daily orders
- Repeat-purchase rate using unique customer IDs
- Delivery delays compared with review scores

The queries use SQL features including common table expressions (CTEs), window functions, aggregations, and date operations.

### 9. Key Metrics

| Metric | Result |
|---|---:|
| Repeat-purchase rate | 3.00% |
| Late-delivery rate | 6.77% |
| Payment mismatch rate among comparable orders | 0.26% |
| Mismatched orders | 260 |

Revenue is calculated using product item prices for delivered orders, excluding freight charges. It should not be interpreted as profit.

### 10. North Star Metric

**Monthly Delivered Item Revenue**

Formula:

`SUM(item price) for delivered orders grouped by purchase month`

This metric tracks the value of products associated with delivered orders. It is supported by repeat-purchase rate, late-delivery rate, and payment-reconciliation quality.

### 11. Limitations and Next Steps

Payment-reconciliation exceptions remain unresolved. The pipeline correctly flags the issue, but