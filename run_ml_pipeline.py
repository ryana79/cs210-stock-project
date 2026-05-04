"""Run the Gian-side machine learning pipeline in one command.

Usage:
    python3 run_ml_pipeline.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    ("Engineer model features", "src/models/feature_engineering.py"),
    ("Train and evaluate models", "src/models/train_models.py"),
]


def run_step(label: str, script: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  STEP: {label}")
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
        print(f"\nFAILED: {label} (exit code {result.returncode})")
        sys.exit(result.returncode)

    print(f"\n  Completed in {elapsed:.1f}s")
    sys.stdout.flush()


def main() -> None:
    print("=" * 60)
    print("  CS 210 STOCK ML PIPELINE")
    print(f"  Running {len(STEPS)} steps")
    print("=" * 60)

    pipeline_start = time.time()
    for label, script in STEPS:
        run_step(label, script)

    total = time.time() - pipeline_start
    print(f"\n{'=' * 60}")
    print(f"  ALL STEPS COMPLETE - total time: {total:.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
