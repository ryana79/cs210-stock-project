from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import BASE_PRICE_COLUMNS, DEFAULT_TICKERS

DEFAULT_START = "2018-01-01"
DEFAULT_END = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download historical daily stock data from Yahoo Finance."
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help="Ticker symbols to download.",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START,
        help="Start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end",
        default=DEFAULT_END,
        help="Optional end date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        # Recent yfinance versions return a MultiIndex even for one ticker.
        # For this project we download one ticker at a time, so the price field
        # level is the stable column name we want to keep.
        df.columns = [str(column[0]) for column in df.columns.to_flat_index()]

    renamed = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Adj_Close": "adj_close",
        "Volume": "volume",
    }
    return df.rename(columns=renamed)


def download_ticker_data(ticker: str, start: str, end: str | None) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No rows returned for ticker {ticker}.")

    df = df.reset_index()
    df = normalize_columns(df)

    missing = [column for column in BASE_PRICE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Ticker {ticker} is missing required columns: {missing}")

    df = df[BASE_PRICE_COLUMNS].copy()
    df["ticker"] = ticker
    return df


def save_raw_csv(df: pd.DataFrame, ticker: str, output_dir: Path) -> Path:
    output_path = output_dir / f"{ticker.lower()}_raw.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    args = parse_args()
    raw_dir = project_root() / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading daily stock data for: {', '.join(args.tickers)}")
    print(f"Date range start: {args.start}")
    if args.end:
        print(f"Date range end: {args.end}")

    for ticker in args.tickers:
        df = download_ticker_data(ticker=ticker, start=args.start, end=args.end)
        output_path = save_raw_csv(df=df, ticker=ticker, output_dir=raw_dir)
        print(f"Saved {len(df)} rows to {output_path}")


if __name__ == "__main__":
    main()
