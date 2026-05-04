"""Self-contained smoke test that proves the cleaning pipeline catches dirty data.

Generates a small synthetic raw CSV with deliberate corruption, runs the
production cleaner against it, and asserts that every dirty row is removed.

Run from the project root:
    python3 src/data/test_cleaning_on_dirty_fixture.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clean_data import clean_single_file


DIRTY_ROWS = pd.DataFrame(
    [
        {"date": "2020-01-02", "open": 100.0, "high": 105.0, "low": 99.0,
         "close": 104.0, "adj_close": 104.0, "volume": 1_000_000, "ticker": "TEST"},
        {"date": "2020-01-02", "open": 100.0, "high": 105.0, "low": 99.0,
         "close": 104.0, "adj_close": 104.0, "volume": 1_000_000, "ticker": "TEST"},
        {"date": "2020-01-03", "open": 101.0, "high": 106.0, "low": 100.0,
         "close": None, "adj_close": 105.0, "volume": 900_000, "ticker": "TEST"},
        {"date": "2020-01-06", "open": -10.0, "high": -5.0, "low": -12.0,
         "close": -8.0, "adj_close": -8.0, "volume": 500_000, "ticker": "TEST"},
        {"date": "2020-01-07", "open": 200.0, "high": 95.0, "low": 100.0,
         "close": 102.0, "adj_close": 102.0, "volume": 800_000, "ticker": "TEST"},
        {"date": "2020-01-08", "open": 103.0, "high": 110.0, "low": 102.0,
         "close": 120.0, "adj_close": 120.0, "volume": 750_000, "ticker": "TEST"},
        {"date": "2020-01-09", "open": 104.0, "high": 109.0, "low": 103.0,
         "close": 105.0, "adj_close": 105.0, "volume": 1_100_000, "ticker": "TEST"},
        {"date": "2020-01-10", "open": 105.0, "high": 108.0, "low": 104.0,
         "close": 106.0, "adj_close": 106.0, "volume": 1_200_000, "ticker": "TEST"},
    ]
)

EXPECTED_CLEAN_ROWS = 3
EXPECTED_DIRTY_REMOVED = 5


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        fixture_path = Path(tmp) / "test_raw.csv"
        DIRTY_ROWS.to_csv(fixture_path, index=False)

        cleaned, audit = clean_single_file(fixture_path)
        actual_failed = sum(row["rows_failed"] for row in audit)

        print(f"Input rows:               {len(DIRTY_ROWS)}")
        print(f"Cleaned rows:             {len(cleaned)}")
        print(f"Total dirty rows removed: {actual_failed}")
        print()
        print("Per-check breakdown:")
        for row in audit:
            print(
                f"  - {row['check_name']:<35} "
                f"failed={row['rows_failed']}  action={row['action']}"
            )

        assert len(cleaned) == EXPECTED_CLEAN_ROWS, (
            f"Expected {EXPECTED_CLEAN_ROWS} clean rows, got {len(cleaned)}"
        )
        assert actual_failed == EXPECTED_DIRTY_REMOVED, (
            f"Expected {EXPECTED_DIRTY_REMOVED} removals, got {actual_failed}"
        )

        print()
        print("PASSED: cleaning pipeline correctly removed all dirty rows.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
