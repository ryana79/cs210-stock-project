from __future__ import annotations

from pathlib import Path

import pandas as pd

FEATURE_COLUMNS = [
    "daily_return",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_4",
    "lag_5",
    "ma_5",
    "ma_10",
    "ma_20",
    "volatility_10",
    "volume_change",
]
TARGET_COLUMN = "target_next_day_up"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_cleaned_data(cleaned_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(cleaned_csv)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    featured_df = df.copy()
    grouped_close = featured_df.groupby("ticker")["close"]
    grouped_volume = featured_df.groupby("ticker")["volume"]

    featured_df["daily_return"] = grouped_close.pct_change()
    featured_df["volume_change"] = grouped_volume.pct_change()

    for lag in range(1, 6):
        featured_df[f"lag_{lag}"] = grouped_close.shift(lag)

    for window in (5, 10, 20):
        featured_df[f"ma_{window}"] = grouped_close.transform(
            lambda series: series.rolling(window=window, min_periods=window).mean()
        )

    featured_df["volatility_10"] = featured_df.groupby("ticker")["daily_return"].transform(
        lambda series: series.rolling(window=10, min_periods=10).std()
    )
    featured_df[TARGET_COLUMN] = (
        featured_df.groupby("ticker")["close"].shift(-1) > featured_df["close"]
    ).astype("Int64")

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    featured_df = featured_df.dropna(subset=required_columns).copy()
    featured_df[TARGET_COLUMN] = featured_df[TARGET_COLUMN].astype(int)
    featured_df["date"] = featured_df["date"].dt.strftime("%Y-%m-%d")
    return featured_df.reset_index(drop=True)


def summarize_featured_data(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("ticker", as_index=False)
        .agg(
            row_count=("date", "count"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            up_days=(TARGET_COLUMN, "sum"),
        )
        .sort_values("ticker")
    )
    summary["up_day_rate"] = (summary["up_days"] / summary["row_count"]).round(3)
    return summary


def main() -> None:
    root = project_root()
    cleaned_csv = root / "data" / "processed" / "cleaned_stock_prices.csv"
    processed_dir = root / "data" / "processed"
    featured_csv = processed_dir / "featured_stock_prices.csv"
    summary_csv = processed_dir / "featured_data_summary.csv"

    if not cleaned_csv.exists():
        raise FileNotFoundError(
            f"Missing cleaned dataset at {cleaned_csv}. Run clean_data.py first."
        )

    processed_dir.mkdir(parents=True, exist_ok=True)
    featured_df = engineer_features(load_cleaned_data(cleaned_csv))
    featured_df.to_csv(featured_csv, index=False)
    summarize_featured_data(featured_df).to_csv(summary_csv, index=False)

    print(f"Saved featured data to {featured_csv}")
    print(f"Saved feature summary to {summary_csv}")
    print(f"Feature-engineered rows available for modeling: {len(featured_df)}")


if __name__ == "__main__":
    main()
