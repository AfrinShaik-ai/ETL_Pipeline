
from pathlib import Path
import duckdb

project_dir = Path(__file__).resolve().parent.parent
db_path = project_dir / "data" / "processed" / "olist.duckdb"

with duckdb.connect(str(db_path), read_only=True) as con:
    tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()

    print("Tables created:")
    for (table_name,) in tables:
        print("-", table_name)

    print("\nFirst five rows from mart_orders:")
    print(
        con.execute("""
            SELECT *
            FROM mart_orders
            LIMIT 5
        """).df().to_string(index=False)
    )
