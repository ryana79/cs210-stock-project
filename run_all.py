"""Run the entire CS 210 project pipeline (data + ML) in one command.

Usage:
    python3 run_all.py                 # run all 8 steps
    python3 run_all.py --skip-download # reuse existing raw data
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    ("1/8  Download raw data", "src/data/download_data.py"),
    ("2/8  Clean and validate", "src/data/clean_data.py"),
    ("3/8  Create SQLite database", "src/db/create_database.py"),
    ("4/8  Generate EDA figures", "src/analysis/generate_eda.py"),
    ("5/8  Run SQL report queries", "src/db/run_queries.py"),
    ("6/8  Export EDA summary", "src/analysis/export_eda_summary.py"),
    ("7/8  Engineer ML features", "src/models/feature_engineering.py"),
    ("8/8  Train and evaluate models", "src/models/train_models.py"),
]


def run_step(label: str, script: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  STEP {label}")
    print(f"  Script: {script}")
    print(f"{'=' * 60}\n")
    sys.stdout.flush()

    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        cwd=Path(__file__).resolve().parent,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  FAILED: {label} (exit code {result.returncode})")
        sys.exit(result.returncode)

    print(f"\n  Completed in {elapsed:.1f}s")
    sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full CS 210 project pipeline (data + ML).",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the download step and reuse existing raw CSVs.",
    )
    args = parser.parse_args()

    steps = STEPS if not args.skip_download else STEPS[1:]

    print("=" * 60)
    print("  CS 210 STOCK ANALYSIS — FULL PROJECT PIPELINE")
    print(f"  Running {len(steps)} steps (data management + ML)")
    print("=" * 60)

    pipeline_start = time.time()
    for label, script in steps:
        run_step(label, script)

    total = time.time() - pipeline_start
    print(f"\n{'=' * 60}")
    print(f"  ALL {len(steps)} STEPS COMPLETE — total time: {total:.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
