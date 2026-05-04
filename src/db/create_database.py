from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
from constants import TICKER_TO_SECTOR


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_schema(schema_path: Path) -> str:
    return schema_path.read_text()


def insert_stocks(conn: sqlite3.Connection, stocks_df: pd.DataFrame) -> dict[str, int]:
    cursor = conn.cursor()
    ticker_to_id: dict[str, int] = {}

    for row in stocks_df.itertuples(index=False):
        sector = TICKER_TO_SECTOR.get(row.ticker, "Unknown")
        cursor.execute(
            """
            INSERT INTO stocks (ticker, company_name, sector)
            VALUES (?, ?, ?)
            """,
            (row.ticker, row.company_name, sector),
        )
        ticker_to_id[row.ticker] = cursor.lastrowid

    return ticker_to_id


def insert_daily_prices(
    conn: sqlite3.Connection,
    prices_df: pd.DataFrame,
    ticker_to_id: dict[str, int],
) -> None:
    records = [
        (
            ticker_to_id[row.ticker],
            row.date,
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            float(row.adj_close),
            int(row.volume),
        )
        for row in prices_df.itertuples(index=False)
    ]

    conn.executemany(
        """
        INSERT INTO daily_prices (
            stock_id,
            trade_date,
            open_price,
            high_price,
            low_price,
            close_price,
            adjusted_close,
            volume
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )


def main() -> None:
    root = project_root()
    cleaned_csv = root / "data" / "processed" / "cleaned_stock_prices.csv"
    database_path = root / "data" / "processed" / "stocks.db"
    schema_path = root / "sql" / "schema.sql"

    if not cleaned_csv.exists():
        raise FileNotFoundError(
            f"Missing cleaned dataset at {cleaned_csv}. Run clean_data.py first."
        )

    prices_df = pd.read_csv(cleaned_csv)
    stocks_df = (
        prices_df[["ticker", "company_name"]]
        .drop_duplicates()
        .sort_values("ticker")
        .reset_index(drop=True)
    )

    with sqlite3.connect(database_path) as conn:
        conn.executescript(load_schema(schema_path))
        ticker_to_id = insert_stocks(conn, stocks_df)
        insert_daily_prices(conn, prices_df, ticker_to_id)
        conn.commit()

        db_row_count = pd.read_sql_query(
            "SELECT COUNT(*) AS cnt FROM daily_prices", conn
        ).iloc[0]["cnt"]

    print(f"Created SQLite database at {database_path}")
    print(f"Inserted {len(stocks_df)} stocks")
    print(f"Inserted {len(prices_df)} daily price rows")

    if db_row_count != len(prices_df):
        raise RuntimeError(
            f"Row count mismatch: CSV has {len(prices_df)} rows but "
            f"database has {db_row_count} rows."
        )
    print(f"Verified: CSV and database row counts match ({db_row_count})")


if __name__ == "__main__":
    main()
