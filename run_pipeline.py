"""Run the entire Ryan-side data pipeline in one command.

Usage:
    python3 run_pipeline.py           # run all steps
    python3 run_pipeline.py --skip-download   # reuse existing raw data
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    ("Download raw data", "src/data/download_data.py"),
    ("Clean and validate", "src/data/clean_data.py"),
    ("Create SQLite database", "src/db/create_database.py"),
    ("Generate EDA figures", "src/analysis/generate_eda.py"),
    ("Run SQL report queries", "src/db/run_queries.py"),
    ("Export EDA summary", "src/analysis/export_eda_summary.py"),
]


def run_step(label: str, script: str) -> None:
    print(f"\n{'='*60}")
    print(f"  STEP: {label}")
    print(f"  Script: {script}")
    print(f"{'='*60}\n")
    sys.stdout.flush()

    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        cwd=Path(__file__).resolve().parent,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\nFAILED: {label} (exit code {result.returncode})")
        sys.exit(result.returncode)

    print(f"\n  Completed in {elapsed:.1f}s")
    sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full data pipeline.")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the download step and reuse existing raw CSVs.",
    )
    args = parser.parse_args()

    steps = STEPS if not args.skip_download else STEPS[1:]

    print("=" * 60)
    print("  CS 210 STOCK ANALYSIS PIPELINE")
    print(f"  Running {len(steps)} steps")
    print("=" * 60)

    pipeline_start = time.time()
    for label, script in steps:
        run_step(label, script)

    total = time.time() - pipeline_start
    print(f"\n{'='*60}")
    print(f"  ALL STEPS COMPLETE — total time: {total:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
