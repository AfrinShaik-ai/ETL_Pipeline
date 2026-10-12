
from pathlib import Path
import csv

# Locate the raw CSV folder relative to this script.
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

def inspect_csv(file_path):
    """Print the column names and number of data rows."""
    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)

        headers = next(reader, None)

        if headers is None:
            print(f"EMPTY FILE: {file_path.name}")
            return

        row_count = sum(1 for _ in reader)

    print(f"\nFile: {file_path.name}")
    print(f"Columns ({len(headers)}): {headers}")
    print(f"Data rows: {row_count:,}")

def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data folder not found: {RAW_DIR}"
        )

    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR}"
        )

    print(f"Found {len(csv_files)} CSV files.")

    for file_path in csv_files:
        try:
            inspect_csv(file_path)
        except Exception as error:
            raise RuntimeError(
                f"Failed to inspect {file_path.name}: {error}"
            ) from error

if __name__ == "__main__":
    main()
