"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 01: Pandas vs. Polars
================================================================================
Measures execution latency, CPU utilization, energy consumption (Joules/Wh),
and estimated carbon emissions (gCO2eq) on a 5-million-row aggregation pipeline.
================================================================================
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import polars as pl

# Ensure local ecotrace package is resolvable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ecotrace import EcoTrace

NUM_ROWS = 2_000_000  # Default to 2M for balanced memory & execution speed
DATASET_PATH = os.path.join(os.path.dirname(__file__), "benchmark_data.parquet")


def generate_dataset(num_rows: int = NUM_ROWS) -> None:
    """Generates synthetic e-commerce transaction dataset in Apache Parquet format."""
    if os.path.exists(DATASET_PATH):
        print(f"[+] Dataset '{DATASET_PATH}' already exists. Skipping generation.")
        return

    print(f"[*] Generating synthetic dataset ({num_rows:,} rows)...")
    np.random.seed(42)
    categories = [f"category_{i}" for i in range(1, 51)]
    countries = ["US", "DE", "GB", "FR", "JP", "IN", "BR", "CA"]

    data = {
        "user_id": np.random.randint(1, 1_000_000, size=num_rows),
        "category": np.random.choice(categories, size=num_rows),
        "country": np.random.choice(countries, size=num_rows),
        "amount": np.random.uniform(5.0, 500.0, size=num_rows).round(2),
        "quantity": np.random.randint(1, 10, size=num_rows),
    }
    df = pd.DataFrame(data)
    df.to_parquet(DATASET_PATH, engine="pyarrow", index=False)
    print(f"[+] Parquet dataset created successfully ({os.path.getsize(DATASET_PATH) / 1024 / 1024:.2f} MB)")


def run_pandas_pipeline() -> int:
    """Executes filtering, multi-aggregation, and sorting via Pandas."""
    df = pd.read_parquet(DATASET_PATH)
    filtered = df[(df["country"].isin(["US", "DE", "GB"])) & (df["amount"] > 50.0)]
    result = (
        filtered.groupby("category")
        .agg(
            total_revenue=("amount", "sum"),
            avg_quantity=("quantity", "mean"),
            transaction_count=("user_id", "count"),
        )
        .sort_values(by="total_revenue", ascending=False)
    )
    return len(result)


def run_polars_pipeline() -> int:
    """Executes filtering, multi-aggregation, and sorting via Polars (Lazy API)."""
    q = (
        pl.scan_parquet(DATASET_PATH)
        .filter((pl.col("country").is_in(["US", "DE", "GB"])) & (pl.col("amount") > 50.0))
        .group_by("category")
        .agg(
            [
                pl.col("amount").sum().alias("total_revenue"),
                pl.col("quantity").mean().alias("avg_quantity"),
                pl.col("user_id").count().alias("transaction_count"),
            ]
        )
        .sort("total_revenue", descending=True)
    )
    result = q.collect()
    return len(result)


def main() -> None:
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: Pandas vs. Polars (Energy & Carbon Efficiency)")
    print("=" * 70)

    generate_dataset()
    eco = EcoTrace(check_updates=False, run_label="DataEngine-Benchmark")

    # Warm-up run (optional caching)
    print("\n[*] Initializing warm-up...")
    _ = run_polars_pipeline()

    print("\n" + "-" * 70)
    print(" [1/2] RUNNING PANDAS PIPELINE WITH ECOTRACE INSTRUMENTATION")
    print("-" * 70)
    with eco.track_block("pandas_pipeline"):
        t0 = time.perf_counter()
        pandas_res = run_pandas_pipeline()
        pandas_duration = time.perf_counter() - t0

    print(f"  -> Pandas Execution Time: {pandas_duration:.4f} seconds (Result Rows: {pandas_res})")

    print("\n" + "-" * 70)
    print(" [2/2] RUNNING POLARS PIPELINE WITH ECOTRACE INSTRUMENTATION")
    print("-" * 70)
    with eco.track_block("polars_pipeline"):
        t0 = time.perf_counter()
        polars_res = run_polars_pipeline()
        polars_duration = time.perf_counter() - t0

    print(f"  -> Polars Execution Time: {polars_duration:.4f} seconds (Result Rows: {polars_res})")

    print("\n" + "=" * 70)
    print(" Benchmark completed. EcoTrace session summary will display below.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
