"""
Polars profiling example with EcoTrace.

Measures CPU utilization and carbon footprint for equivalent eager and lazy
Polars pipelines over a synthetic in-memory dataset, using both the
``@eco.track`` decorator and the ``eco.track_block()`` context manager. The
dataset uses a fixed seed, so the script runs offline and needs no downloads.

See docs/USAGE.md ("Profiling Polars Workloads") for the sampling-accuracy
caveats this example is built around, and
docs/benchmarks/01_pandas_vs_polars.md for a deeper Pandas-vs-Polars energy
comparison.

Requires: polars
"""

from __future__ import annotations

import os
import random
import sys
import tempfile

try:
    import polars as pl
except ImportError:
    sys.exit("This example needs Polars. Install it with: pip install polars")

from ecotrace import EcoTrace

N_ROWS = 2_000_000
N_CATEGORIES = 50
COUNTRIES = ["US", "DE", "GB", "TR", "FR"]
SEED = 42
REGION = "GLOBAL"


def build_dataset(n_rows: int = N_ROWS) -> pl.DataFrame:
    """Build a synthetic, fixed-seed transaction dataset."""
    rng = random.Random(SEED)
    return pl.DataFrame({
        "id": range(n_rows),
        "category": [rng.randrange(N_CATEGORIES) for _ in range(n_rows)],
        "country": [rng.choice(COUNTRIES) for _ in range(n_rows)],
        "amount": [rng.uniform(1.0, 1000.0) for _ in range(n_rows)],
    })


def eager_groupby(df: pl.DataFrame) -> pl.DataFrame:
    """Eager categorical group-by and aggregation."""
    return df.group_by("category").agg(
        pl.col("amount").sum().alias("total"),
        pl.col("amount").mean().alias("avg"),
    )


def eager_join(df: pl.DataFrame) -> pl.DataFrame:
    """Eager join against a small per-category weight lookup table."""
    weights = pl.DataFrame({
        "category": range(N_CATEGORIES),
        "weight": [float(c) for c in range(N_CATEGORIES)],
    })
    return df.join(weights, on="category")


def lazy_pipeline(df: pl.DataFrame) -> pl.DataFrame:
    """Build and collect a lazy filter -> group_by -> sort pipeline.

    ``collect()`` is what actually executes a LazyFrame; building the query
    with ``.lazy()`` does no work by itself. It must run inside the tracked
    scope, or the measurement would cover an empty query plan instead of the
    computation it describes.
    """
    query = (
        df.lazy()
        .filter(pl.col("country").is_in(["US", "DE", "GB"]))
        .group_by("category")
        .agg(
            pl.col("amount").sum().alias("total"),
            pl.col("amount").mean().alias("avg"),
        )
        .sort("total", descending=True)
    )
    return query.collect()


def main() -> None:
    """Profile eager and lazy Polars pipelines with both tracking styles."""
    df = build_dataset()

    # EcoTrace.track / track_block always write their CSV audit log
    # ("ecotrace_log.csv") relative to the current working directory, so the
    # whole run happens inside a temporary directory to keep the repo clean.
    out_dir = tempfile.mkdtemp(prefix="ecotrace_polars_")
    original_cwd = os.getcwd()
    os.chdir(out_dir)
    try:
        eco = EcoTrace(region_code=REGION, check_updates=False)

        # Context manager usage: one tracked block per pipeline stage.
        with eco.track_block("eager_groupby"):
            grouped = eager_groupby(df)

        with eco.track_block("eager_join"):
            joined = eager_join(df)

        with eco.track_block("lazy_pipeline_collect"):
            lazy_result = lazy_pipeline(df)

        # Decorator usage: wrap a function instead of a bare block.
        @eco.track
        def decorated_groupby() -> pl.DataFrame:
            return eager_groupby(df)

        decorated_result = decorated_groupby()

        report_path = os.path.join(out_dir, "polars_report.json")
        eco.export_json(report_path)

        print(f"Eager groupby rows    : {grouped.height}")
        print(f"Eager join rows       : {joined.height}")
        print(f"Lazy pipeline rows    : {lazy_result.height}")
        print(f"Decorated groupby rows: {decorated_result.height}")
        print(f"Total carbon          : {eco.total_carbon:.8f} gCO2")
        print(f"Output directory      : {out_dir}")
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
