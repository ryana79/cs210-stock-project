"""Clean and validate raw Yahoo Finance CSVs.

The pipeline performs two categories of checks:

1. **Hard checks** (drop rows that fail) - these correct corrupt data that
   would break downstream analysis if left in:
     - Duplicate (ticker, date) rows
     - Missing required values
     - Negative or zero prices
     - Price-relationship invariants (low <= open/close <= high; low <= high)

2. **Soft checks** (flag and report only) - these surface suspicious data
   that may still be valid but warrants investigator attention:
     - Zero-volume trading days (possible halts)
     - Extreme single-day returns (>50%, likely missed split or data error)
     - Calendar gaps > 5 days (possible missing data)

Every check writes a row to ``data_validation_report.csv`` so the cleaning
behaviour is auditable even when no rows are removed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import NUMERIC_COLUMNS, RAW_REQUIRED_COLUMNS, TICKER_TO_COMPANY

PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close"]
EXTREME_RETURN_THRESHOLD_PCT = 50.0
DATE_GAP_THRESHOLD_DAYS = 5


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def list_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(raw_dir.glob("*_raw.csv"))


def _record(check: str, evaluated: int, failed: int, action: str, description: str) -> dict:
    return {
        "check_name": check,
        "rows_evaluated": int(evaluated),
        "rows_failed": int(failed),
        "action": action,
        "description": description,
    }


def clean_single_file(path: Path) -> tuple[pd.DataFrame, list[dict]]:
    """Clean a single raw CSV and return (cleaned_df, per-check audit rows)."""
    df = pd.read_csv(path)
    df.columns = [column.strip().lower() for column in df.columns]
    initial_row_count = len(df)
    audit: list[dict] = []

    missing = [column for column in RAW_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    audit.append(
        _record(
            "schema_required_columns_present",
            evaluated=len(RAW_REQUIRED_COLUMNS),
            failed=0,
            action="raise_if_missing",
            description=(
                "All 8 required columns (date, OHLC, adj_close, volume, ticker) "
                "must be present; raises ValueError if not."
            ),
        )
    )

    df = df[RAW_REQUIRED_COLUMNS].copy()
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["company_name"] = df["ticker"].map(TICKER_TO_COMPANY).fillna("Unknown Company")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    before = len(df)
    df = df.drop_duplicates(subset=["ticker", "date"]).sort_values(["ticker", "date"])
    duplicates_removed = before - len(df)
    audit.append(
        _record(
            "duplicate_ticker_date",
            evaluated=before,
            failed=duplicates_removed,
            action="drop_duplicates",
            description=(
                "Each (ticker, date) pair must be unique to satisfy the "
                "database UNIQUE constraint and prevent double-counting."
            ),
        )
    )

    before = len(df)
    df = df.dropna(subset=["date", *NUMERIC_COLUMNS])
    nulls_removed = before - len(df)
    audit.append(
        _record(
            "null_required_values",
            evaluated=before,
            failed=nulls_removed,
            action="drop_rows",
            description="Rows missing any required price/volume/date are dropped.",
        )
    )

    before = len(df)
    bad_price = (df[PRICE_COLUMNS] <= 0).any(axis=1)
    df = df.loc[~bad_price].copy()
    negative_prices = before - len(df)
    audit.append(
        _record(
            "negative_or_zero_prices",
            evaluated=before,
            failed=negative_prices,
            action="drop_rows",
            description=(
                "Stock prices must be strictly positive; zero/negative prices "
                "indicate data corruption."
            ),
        )
    )

    before = len(df)
    invariant_violations = (
        (df["low"] > df["high"])
        | (df["open"] > df["high"]) | (df["open"] < df["low"])
        | (df["close"] > df["high"]) | (df["close"] < df["low"])
    )
    invariants_failed = int(invariant_violations.sum())
    df = df.loc[~invariant_violations].copy()
    audit.append(
        _record(
            "price_relationship_invariants",
            evaluated=before,
            failed=invariants_failed,
            action="drop_rows",
            description=(
                "Within a trading day, open and close must lie within [low, high] "
                "and low <= high; any violation is impossible and indicates corruption."
            ),
        )
    )

    print(
        f"  {path.name}: {initial_row_count} raw -> "
        f"{duplicates_removed} dup, {nulls_removed} null, "
        f"{negative_prices} bad-price, {invariants_failed} invariant-fail "
        f"-> {len(df)} kept"
    )

    df["volume"] = df["volume"].astype("int64")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    cleaned = df.reset_index(drop=True)

    for row in audit:
        row["source_file"] = path.name
    return cleaned, audit


def soft_quality_checks(df: pd.DataFrame) -> list[dict]:
    """Run advisory checks on the cleaned dataset (no rows dropped)."""
    audit: list[dict] = []

    audit.append(
        _record(
            "zero_volume_days",
            evaluated=len(df),
            failed=int((df["volume"] == 0).sum()),
            action="flag_only",
            description=(
                "Zero-volume days can indicate trading halts or data gaps; "
                "flagged for review but not dropped."
            ),
        )
    )

    sorted_df = df.sort_values(["ticker", "date"]).copy()
    sorted_df["prev_close"] = sorted_df.groupby("ticker")["close"].shift(1)
    sorted_df["pct_change_abs"] = (
        (sorted_df["close"] - sorted_df["prev_close"]).abs()
        / sorted_df["prev_close"] * 100
    )
    extreme = sorted_df["pct_change_abs"] > EXTREME_RETURN_THRESHOLD_PCT
    audit.append(
        _record(
            "extreme_daily_returns_gt_50pct",
            evaluated=int(sorted_df["pct_change_abs"].notna().sum()),
            failed=int(extreme.fillna(False).sum()),
            action="flag_only",
            description=(
                "Single-day moves above 50% almost always indicate an unadjusted "
                "split or data error rather than a real return."
            ),
        )
    )

    parsed = sorted_df.copy()
    parsed["date_parsed"] = pd.to_datetime(parsed["date"])
    parsed["gap_days"] = parsed.groupby("ticker")["date_parsed"].diff().dt.days
    gaps = (parsed["gap_days"] > DATE_GAP_THRESHOLD_DAYS).fillna(False)
    audit.append(
        _record(
            "date_gap_above_5_calendar_days",
            evaluated=int(parsed["gap_days"].notna().sum()),
            failed=int(gaps.sum()),
            action="flag_only",
            description=(
                "Calendar gaps > 5 days within a ticker may indicate missing "
                "trading-day records (excludes normal weekend/holiday gaps)."
            ),
        )
    )

    return audit


def build_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("ticker", as_index=False)
        .agg(
            row_count=("date", "count"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            avg_close=("close", "mean"),
            avg_volume=("volume", "mean"),
        )
        .sort_values("ticker")
    )
    summary["avg_close"] = summary["avg_close"].round(2)
    summary["avg_volume"] = summary["avg_volume"].round(0).astype("int64")
    return summary


def aggregate_per_file_audits(per_file_audits: list[list[dict]]) -> pd.DataFrame:
    """Sum per-file hard-check audit rows into a single dataset-wide report."""
    flat = [row for batch in per_file_audits for row in batch]
    if not flat:
        return pd.DataFrame()
    audit_df = pd.DataFrame(flat)
    grouped = (
        audit_df.groupby("check_name", as_index=False)
        .agg(
            rows_evaluated=("rows_evaluated", "sum"),
            rows_failed=("rows_failed", "sum"),
            action=("action", "first"),
            description=("description", "first"),
        )
    )
    return grouped


def main() -> None:
    root = project_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_files = list_raw_files(raw_dir)
    if not raw_files:
        raise FileNotFoundError(
            f"No raw CSV files found in {raw_dir}. Run download_data.py first."
        )

    cleaned_frames: list[pd.DataFrame] = []
    per_file_audits: list[list[dict]] = []
    for path in raw_files:
        cleaned, audit = clean_single_file(path)
        cleaned_frames.append(cleaned)
        per_file_audits.append(audit)

    cleaned_df = pd.concat(cleaned_frames, ignore_index=True)

    hard_audit_df = aggregate_per_file_audits(per_file_audits)
    soft_audit_df = pd.DataFrame(soft_quality_checks(cleaned_df))
    validation_df = pd.concat([hard_audit_df, soft_audit_df], ignore_index=True)
    column_order = ["check_name", "rows_evaluated", "rows_failed", "action", "description"]
    validation_df = validation_df[column_order]

    cleaned_output = processed_dir / "cleaned_stock_prices.csv"
    quality_output = processed_dir / "data_quality_report.csv"
    validation_output = processed_dir / "data_validation_report.csv"

    cleaned_df.to_csv(cleaned_output, index=False)
    build_quality_report(cleaned_df).to_csv(quality_output, index=False)
    validation_df.to_csv(validation_output, index=False)

    total_failed = int(validation_df["rows_failed"].sum())
    print()
    print(f"Saved cleaned data to {cleaned_output}")
    print(f"Saved data quality report to {quality_output}")
    print(f"Saved data validation report to {validation_output}")
    print(f"Total cleaned rows: {len(cleaned_df)}")
    print(
        f"Validation: {len(validation_df)} quality rules ran, "
        f"{total_failed} total row-level violations across the dataset."
    )


if __name__ == "__main__":
    main()
