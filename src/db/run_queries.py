from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


QUERY_CATALOG = {
    "database_row_counts.csv": """
        SELECT
            s.ticker,
            s.company_name,
            COUNT(*) AS row_count
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """,
    "latest_close_prices.csv": """
        SELECT
            s.ticker,
            dp.trade_date,
            ROUND(dp.close_price, 2) AS close_price
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        WHERE (dp.stock_id, dp.trade_date) IN (
            SELECT stock_id, MAX(trade_date)
            FROM daily_prices
            GROUP BY stock_id
        )
        ORDER BY s.ticker
    """,
    "stock_summary_stats.csv": """
        SELECT
            s.ticker,
            ROUND(AVG(dp.close_price), 2) AS avg_close_price,
            ROUND(MIN(dp.close_price), 2) AS min_close_price,
            ROUND(MAX(dp.close_price), 2) AS max_close_price,
            ROUND(AVG(dp.volume), 2) AS avg_volume
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """,
    "yearly_average_close.csv": """
        SELECT
            s.ticker,
            SUBSTR(dp.trade_date, 1, 4) AS year,
            ROUND(AVG(dp.close_price), 2) AS avg_close_price
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        GROUP BY s.ticker, year
        ORDER BY s.ticker, year
    """,
    "price_range_by_stock.csv": """
        SELECT
            s.ticker,
            ROUND(MIN(dp.close_price), 2) AS min_close,
            ROUND(MAX(dp.close_price), 2) AS max_close,
            ROUND(MAX(dp.close_price) - MIN(dp.close_price), 2) AS price_range
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """,
    "date_coverage_by_stock.csv": """
        SELECT
            s.ticker,
            MIN(dp.trade_date) AS first_date,
            MAX(dp.trade_date) AS last_date,
            COUNT(DISTINCT dp.trade_date) AS trading_days
        FROM daily_prices dp
        JOIN stocks s
            ON dp.stock_id = s.stock_id
        GROUP BY s.ticker
        ORDER BY s.ticker
    """,
    "top_10_daily_gains.csv": """
        SELECT
            s.ticker,
            dp.trade_date,
            ROUND(dp.close_price, 2) AS close_price,
            ROUND(prev.close_price, 2) AS prev_close,
            ROUND(
                (dp.close_price - prev.close_price) / prev.close_price * 100, 2
            ) AS daily_return_pct
        FROM daily_prices dp
        JOIN stocks s ON dp.stock_id = s.stock_id
        JOIN daily_prices prev ON dp.stock_id = prev.stock_id
            AND prev.trade_date = (
                SELECT MAX(p2.trade_date)
                FROM daily_prices p2
                WHERE p2.stock_id = dp.stock_id
                  AND p2.trade_date < dp.trade_date
            )
        ORDER BY daily_return_pct DESC
        LIMIT 10
    """,
    "top_10_daily_losses.csv": """
        SELECT
            s.ticker,
            dp.trade_date,
            ROUND(dp.close_price, 2) AS close_price,
            ROUND(prev.close_price, 2) AS prev_close,
            ROUND(
                (dp.close_price - prev.close_price) / prev.close_price * 100, 2
            ) AS daily_return_pct
        FROM daily_prices dp
        JOIN stocks s ON dp.stock_id = s.stock_id
        JOIN daily_prices prev ON dp.stock_id = prev.stock_id
            AND prev.trade_date = (
                SELECT MAX(p2.trade_date)
                FROM daily_prices p2
                WHERE p2.stock_id = dp.stock_id
                  AND p2.trade_date < dp.trade_date
            )
        ORDER BY daily_return_pct ASC
        LIMIT 10
    """,
    "quarterly_average_close.csv": """
        SELECT
            s.ticker,
            SUBSTR(dp.trade_date, 1, 4) AS year,
            CASE
                WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 3  THEN 'Q1'
                WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 6  THEN 'Q2'
                WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 9  THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,
            COUNT(*) AS trading_days,
            ROUND(AVG(dp.close_price), 2) AS avg_close_price,
            ROUND(AVG(dp.volume), 0) AS avg_volume
        FROM daily_prices dp
        JOIN stocks s ON dp.stock_id = s.stock_id
        GROUP BY s.ticker, year, quarter
        ORDER BY s.ticker, year, quarter
    """,
    "sector_performance_summary.csv": """
        SELECT
            s.sector,
            COUNT(DISTINCT s.ticker) AS stock_count,
            COUNT(*) AS total_trading_days,
            ROUND(AVG(dp.close_price), 2) AS avg_close_price,
            ROUND(AVG(dp.volume), 0) AS avg_daily_volume,
            ROUND(MIN(dp.close_price), 2) AS sector_min_price,
            ROUND(MAX(dp.close_price), 2) AS sector_max_price
        FROM daily_prices dp
        JOIN stocks s ON dp.stock_id = s.stock_id
        GROUP BY s.sector
        ORDER BY s.sector
    """,
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_query(conn: sqlite3.Connection, query: str) -> pd.DataFrame:
    return pd.read_sql_query(query, conn)


def export_query_outputs(conn: sqlite3.Connection, output_dir: Path) -> None:
    for filename, query in QUERY_CATALOG.items():
        df = run_query(conn, query)
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"Saved query output to {output_path}")


def main() -> None:
    root = project_root()
    database_path = root / "data" / "processed" / "stocks.db"
    output_dir = root / "outputs" / "metrics"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not database_path.exists():
        raise FileNotFoundError(
            f"Missing SQLite database at {database_path}. Run create_database.py first."
        )

    with sqlite3.connect(database_path) as conn:
        export_query_outputs(conn, output_dir)


if __name__ == "__main__":
    main()
