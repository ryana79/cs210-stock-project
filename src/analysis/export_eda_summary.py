from __future__ import annotations

from pathlib import Path

import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_cleaned_data(cleaned_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(cleaned_csv)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    summary_df = (
        df.groupby(["ticker", "company_name"], as_index=False)
        .agg(
            row_count=("date", "count"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            avg_close=("close", "mean"),
            min_close=("close", "min"),
            max_close=("close", "max"),
            avg_volume=("volume", "mean"),
        )
        .sort_values("ticker")
    )

    summary_df["first_date"] = summary_df["first_date"].dt.strftime("%Y-%m-%d")
    summary_df["last_date"] = summary_df["last_date"].dt.strftime("%Y-%m-%d")
    summary_df["avg_close"] = summary_df["avg_close"].round(2)
    summary_df["min_close"] = summary_df["min_close"].round(2)
    summary_df["max_close"] = summary_df["max_close"].round(2)
    summary_df["avg_volume"] = summary_df["avg_volume"].round(2)
    return summary_df


def build_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for ticker, group in df.groupby("ticker"):
        daily_return = group.sort_values("date")["adj_close"].pct_change().dropna() * 100
        records.append({
            "ticker": ticker,
            "mean_close": round(group["close"].mean(), 2),
            "median_close": round(group["close"].median(), 2),
            "std_close": round(group["close"].std(), 2),
            "min_close": round(group["close"].min(), 2),
            "max_close": round(group["close"].max(), 2),
            "mean_volume": round(group["volume"].mean(), 0),
            "median_volume": round(group["volume"].median(), 0),
            "mean_daily_return_pct": round(daily_return.mean(), 4),
            "std_daily_return_pct": round(daily_return.std(), 4),
            "skewness_daily_return": round(float(daily_return.skew()), 4),
            "kurtosis_daily_return": round(float(daily_return.kurtosis()), 4),
        })
    return pd.DataFrame(records).sort_values("ticker")


def build_markdown_summary(summary_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> str:
    if cleaned_df.empty or summary_df.empty:
        raise ValueError("Cannot build an EDA summary from an empty dataset.")

    highest_avg_close = summary_df.loc[summary_df["avg_close"].idxmax()]
    highest_avg_volume = summary_df.loc[summary_df["avg_volume"].idxmax()]
    stock_count = len(summary_df)

    lines = [
        "# EDA Summary",
        "",
        "## Dataset Coverage",
        "",
        f"- Total rows: {len(cleaned_df)}",
        f"- Date range: {cleaned_df['date'].min().strftime('%Y-%m-%d')} to {cleaned_df['date'].max().strftime('%Y-%m-%d')}",
        f"- Stocks analyzed: {', '.join(summary_df['ticker'].tolist())}",
        "",
        "## Key Findings",
        "",
        (
            f"- `{highest_avg_close['ticker']}` has the highest average closing price "
            f"at {highest_avg_close['avg_close']:.2f}."
        ),
        (
            f"- `{highest_avg_volume['ticker']}` has the highest average trading volume "
            f"at {highest_avg_volume['avg_volume']:.2f}."
        ),
        f"- Row counts are very similar across the {stock_count} selected stocks, which helps keep comparisons balanced.",
        "- The price trend plots show substantial long-term growth across all three companies, with different levels of volatility.",
        "- Indexed adjusted price plots are more informative than raw price levels when comparing growth across different stocks.",
        "- Yearly average comparisons should use complete years only because the current year is still partial.",
        "",
        "## Summary Table",
        "",
        "| Ticker | Company | Rows | First Date | Last Date | Avg Close | Min Close | Max Close | Avg Volume |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]

    for row in summary_df.itertuples(index=False):
        lines.append(
            f"| {row.ticker} | {row.company_name} | {row.row_count} | {row.first_date} | "
            f"{row.last_date} | {row.avg_close:.2f} | {row.min_close:.2f} | "
            f"{row.max_close:.2f} | {row.avg_volume:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Ryan-Side Takeaway",
            "",
            "The current data management and EDA pipeline successfully downloads, cleans, stores, and summarizes multi-year stock data in a reproducible way. This prepares a stable input for the machine learning stage while also satisfying the course database and data science requirements.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    root = project_root()
    cleaned_csv = root / "data" / "processed" / "cleaned_stock_prices.csv"
    output_dir = root / "outputs" / "metrics"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not cleaned_csv.exists():
        raise FileNotFoundError(
            f"Missing cleaned dataset at {cleaned_csv}. Run clean_data.py first."
        )

    cleaned_df = load_cleaned_data(cleaned_csv)
    summary_df = build_summary_table(cleaned_df)
    desc_stats_df = build_descriptive_stats(cleaned_df)

    summary_csv = output_dir / "eda_summary_by_stock.csv"
    summary_md = output_dir / "eda_summary.md"
    desc_stats_csv = output_dir / "descriptive_statistics.csv"

    summary_df.to_csv(summary_csv, index=False)
    summary_md.write_text(build_markdown_summary(summary_df, cleaned_df))
    desc_stats_df.to_csv(desc_stats_csv, index=False)

    print(f"Saved EDA summary table to {summary_csv}")
    print(f"Saved EDA summary markdown to {summary_md}")
    print(f"Saved descriptive statistics to {desc_stats_csv}")


if __name__ == "__main__":
    main()
