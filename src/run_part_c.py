
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist.duckdb"
SQL_DIR = PROJECT_DIR / "sql"

sql_files = sorted(SQL_DIR.glob("part_c_*.sql"))

if len(sql_files) != 5:
    raise RuntimeError(
        f"Expected 5 Part C SQL files, found {len(sql_files)}"
    )

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    for sql_file in sql_files:
        print("\n" + "=" * 70)
        print(sql_file.name)
        print("=" * 70)

        query = sql_file.read_text(encoding="utf-8")
        cursor = con.execute(query)

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        print(" | ".join(columns))
        for row in rows[:20]:
            print(" | ".join(
                str(value) if value is not None else "NULL"
                for value in row
            ))

        print(f"\nRows returned: {len(rows)}")
        if len(rows) > 20:
            print("Only the first 20 rows are displayed.")
