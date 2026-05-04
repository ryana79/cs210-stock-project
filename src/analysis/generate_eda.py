from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

FIGURE_DPI = 150
PALETTE = {"AAPL": "#1f77b4", "MSFT": "#2ca02c", "TSLA": "#d62728"}
TICKER_LABELS = {
    "AAPL": "Apple (AAPL)",
    "MSFT": "Microsoft (MSFT)",
    "TSLA": "Tesla (TSLA)",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_cleaned_data(cleaned_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(cleaned_csv)
    df["date"] = pd.to_datetime(df["date"])
    df["label"] = df["ticker"].map(TICKER_LABELS)
    return df


def save_current_figure(output_path: Path) -> None:
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()


def format_price_axis(ax: plt.Axes | None = None) -> None:
    ax = ax or plt.gca()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))


def format_volume_axis(ax: plt.Axes | None = None) -> None:
    ax = ax or plt.gca()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:,.0f}M"))


def _styled_legend(ax: plt.Axes | None = None) -> None:
    ax = ax or plt.gca()
    ax.legend(title="Stock", frameon=True, fancybox=True, shadow=False)


def save_close_price_plot(df: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x="date", y="close", hue="label", palette=PALETTE.values())
    plt.title("Closing Price Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Closing Price")
    format_price_axis()
    _styled_legend()
    save_current_figure(output_dir / "closing_price_trends.png")


def save_adjusted_close_plot(df: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x="date", y="adj_close", hue="label", palette=PALETTE.values())
    plt.title("Adjusted Closing Price Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Adjusted Closing Price")
    format_price_axis()
    _styled_legend()
    save_current_figure(output_dir / "adjusted_closing_price_trends.png")


def save_indexed_growth_plot(df: pd.DataFrame, output_dir: Path) -> None:
    indexed_df = df.sort_values(["ticker", "date"]).copy()
    indexed_df["base_adj_close"] = indexed_df.groupby("ticker")["adj_close"].transform("first")
    indexed_df["indexed_growth"] = (indexed_df["adj_close"] / indexed_df["base_adj_close"]) * 100

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=indexed_df, x="date", y="indexed_growth", hue="label", palette=PALETTE.values())
    plt.axhline(y=100, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    plt.title("Indexed Adjusted Closing Price Growth (Base = 100)")
    plt.xlabel("Date")
    plt.ylabel("Indexed Growth")
    _styled_legend()
    save_current_figure(output_dir / "indexed_adjusted_close_growth.png")


def save_volume_plot(df: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x="date", y="volume", hue="label", palette=PALETTE.values())
    plt.title("Trading Volume Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Volume (shares)")
    format_volume_axis()
    _styled_legend()
    save_current_figure(output_dir / "trading_volume_trends.png")


def save_rolling_volume_plot(df: pd.DataFrame, output_dir: Path) -> None:
    rolling_df = df.sort_values(["ticker", "date"]).copy()
    rolling_df["rolling_30d_volume"] = (
        rolling_df.groupby("ticker")["volume"]
        .transform(lambda series: series.rolling(window=30, min_periods=1).mean())
    )

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=rolling_df, x="date", y="rolling_30d_volume", hue="label", palette=PALETTE.values())
    plt.title("30-Day Rolling Average Trading Volume")
    plt.xlabel("Date")
    plt.ylabel("30-Day Avg Volume (shares)")
    format_volume_axis()
    _styled_legend()
    save_current_figure(output_dir / "rolling_30d_volume_trends.png")


def save_data_quality_plot(df: pd.DataFrame, output_dir: Path) -> None:
    quality_df = (
        df.groupby("ticker", as_index=False)
        .agg(row_count=("date", "count"))
        .sort_values("ticker")
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(quality_df["ticker"], quality_df["row_count"], color=list(PALETTE.values()))
    ax.set_title("Row Count Per Stock")
    ax.set_xlabel("Ticker")
    ax.set_ylabel("Number of Daily Records")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 10, f"{int(height):,}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    save_current_figure(output_dir / "row_count_per_stock.png")


def save_average_close_plot(df: pd.DataFrame, output_dir: Path) -> None:
    summary_df = (
        df.groupby("ticker", as_index=False)
        .agg(avg_close=("close", "mean"))
        .sort_values("ticker")
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(summary_df["ticker"], summary_df["avg_close"], color=list(PALETTE.values()))
    ax.set_title("Average Closing Price By Stock")
    ax.set_xlabel("Ticker")
    ax.set_ylabel("Average Closing Price")
    format_price_axis(ax)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 1, f"${height:,.2f}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    save_current_figure(output_dir / "average_closing_price_by_stock.png")


def save_yearly_close_trend_plot(df: pd.DataFrame, output_dir: Path) -> None:
    yearly_df = df.copy()
    yearly_df["year"] = yearly_df["date"].dt.year

    yearly_counts = (
        yearly_df.groupby(["ticker", "year"], as_index=False)
        .agg(row_count=("date", "count"))
    )
    complete_years = yearly_counts.loc[yearly_counts["row_count"] >= 200, "year"].unique()

    yearly_df = (
        yearly_df.groupby(["ticker", "year"], as_index=False)
        .agg(avg_close=("close", "mean"))
        .sort_values(["ticker", "year"])
    )
    yearly_df = yearly_df[yearly_df["year"].isin(complete_years)]
    yearly_df["label"] = yearly_df["ticker"].map(TICKER_LABELS)

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=yearly_df, x="year", y="avg_close", hue="label",
                 palette=PALETTE.values(), marker="o")
    plt.title("Yearly Average Closing Price Trend (Complete Years Only)")
    plt.xlabel("Year")
    plt.ylabel("Average Closing Price")
    plt.xticks(sorted(complete_years))
    format_price_axis()
    _styled_legend()
    save_current_figure(output_dir / "yearly_average_closing_price_trend.png")


def _compute_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    ret_df = df.sort_values(["ticker", "date"]).copy()
    ret_df["daily_return"] = ret_df.groupby("ticker")["adj_close"].pct_change() * 100
    return ret_df.dropna(subset=["daily_return"])


def save_daily_returns_distribution(df: pd.DataFrame, output_dir: Path, ret_df: pd.DataFrame | None = None) -> None:
    if ret_df is None:
        ret_df = _compute_daily_returns(df)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    for ax, (ticker, color) in zip(axes, PALETTE.items()):
        subset = ret_df[ret_df["ticker"] == ticker]["daily_return"]
        ax.hist(subset, bins=80, color=color, alpha=0.7, edgecolor="white", density=True)
        subset.plot.kde(ax=ax, color="black", linewidth=1.2)
        ax.set_title(TICKER_LABELS[ticker])
        ax.set_xlabel("Daily Return (%)")
        ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.8)
        mean_val = subset.mean()
        std_val = subset.std()
        ax.text(0.97, 0.95, f"μ = {mean_val:.2f}%\nσ = {std_val:.2f}%",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    axes[0].set_ylabel("Density")
    fig.suptitle("Daily Returns Distribution", fontsize=14, fontweight="bold")
    save_current_figure(output_dir / "daily_returns_distribution.png")


def save_returns_correlation_heatmap(df: pd.DataFrame, output_dir: Path, ret_df: pd.DataFrame | None = None) -> None:
    if ret_df is None:
        ret_df = _compute_daily_returns(df)
    pivot_df = ret_df.pivot_table(index="date", columns="ticker", values="daily_return")
    corr = pivot_df.corr()

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".3f", cmap="RdYlGn", center=0,
                vmin=-1, vmax=1, square=True, linewidths=1, ax=ax,
                cbar_kws={"shrink": 0.8})
    ax.set_title("Daily Returns Correlation Between Stocks", fontsize=13, fontweight="bold")
    ax.set_xticklabels([TICKER_LABELS.get(t, t) for t in corr.columns])
    ax.set_yticklabels([TICKER_LABELS.get(t, t) for t in corr.index])
    ax.set_xlabel("")
    ax.set_ylabel("")
    save_current_figure(output_dir / "daily_returns_correlation.png")


def save_monthly_returns_boxplot(df: pd.DataFrame, output_dir: Path, ret_df: pd.DataFrame | None = None) -> None:
    if ret_df is None:
        ret_df = _compute_daily_returns(df)
    ret_df = ret_df.copy()
    ret_df["year_month"] = ret_df["date"].dt.to_period("M")
    monthly = (
        ret_df.groupby(["ticker", "year_month"], as_index=False)
        .agg(monthly_return=("daily_return", "sum"))
    )
    monthly["label"] = monthly["ticker"].map(TICKER_LABELS)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=monthly, x="label", y="monthly_return", hue="label",
                palette=list(PALETTE.values()), showfliers=True, fliersize=3, legend=False)
    plt.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    plt.title("Monthly Returns Distribution By Stock")
    plt.xlabel("Stock")
    plt.ylabel("Monthly Return (%)")
    save_current_figure(output_dir / "monthly_returns_boxplot.png")


def main() -> None:
    root = project_root()
    cleaned_csv = root / "data" / "processed" / "cleaned_stock_prices.csv"
    output_dir = root / "outputs" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not cleaned_csv.exists():
        raise FileNotFoundError(
            f"Missing cleaned dataset at {cleaned_csv}. Run clean_data.py first."
        )

    sns.set_theme(style="whitegrid", font_scale=1.05)
    df = load_cleaned_data(cleaned_csv)

    save_close_price_plot(df, output_dir)
    save_adjusted_close_plot(df, output_dir)
    save_indexed_growth_plot(df, output_dir)
    save_volume_plot(df, output_dir)
    save_rolling_volume_plot(df, output_dir)
    save_data_quality_plot(df, output_dir)
    save_average_close_plot(df, output_dir)
    save_yearly_close_trend_plot(df, output_dir)

    ret_df = _compute_daily_returns(df)
    save_daily_returns_distribution(df, output_dir, ret_df=ret_df)
    save_returns_correlation_heatmap(df, output_dir, ret_df=ret_df)
    save_monthly_returns_boxplot(df, output_dir, ret_df=ret_df)

    print(f"Saved 11 EDA figures to {output_dir}")


if __name__ == "__main__":
    main()
