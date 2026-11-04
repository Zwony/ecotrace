"""
Polars workload example with EcoTrace.

Instruments eager group-by, a lazy join collected in memory, and a
streaming ``LazyFrame.collect()`` with ``@eco.track`` and
``eco.track_block``.

Polars runs those kernels on Rust threads that release the GIL.
EcoTrace samples process-wide CPU every 50 ms from a background thread
(``psutil.Process``), so that native work is included in the measurement.
Decorate the function that calls ``collect()``. A function that only
returns a ``LazyFrame`` measures plan construction, not execution.

Requires: polars
    pip install polars
    python examples/polars_workload.py
"""

from __future__ import annotations

import os
import sys

try:
    import polars as pl
except ImportError:
    sys.exit("This example needs Polars. Install it with: pip install polars")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ecotrace import EcoTrace

N_ORDERS = 5_000
CATEGORIES = ("books", "games", "home", "grocery")
REGIONS = ("EU", "US", "APAC")


def sample_frames(n_orders: int = N_ORDERS) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build a small in-memory orders table and a customer dimension."""
    customer_ids = list(range(1, 501))
    customers = pl.DataFrame(
        {
            "customer_id": customer_ids,
            "region": [REGIONS[i % len(REGIONS)] for i in customer_ids],
        }
    )
    orders = pl.DataFrame(
        {
            "order_id": list(range(n_orders)),
            "customer_id": [customer_ids[i % len(customer_ids)] for i in range(n_orders)],
            "category": [CATEGORIES[i % len(CATEGORIES)] for i in range(n_orders)],
            "amount": [float(5 + (i % 50)) for i in range(n_orders)],
        }
    )
    return orders, customers


def eager_groupby(orders: pl.DataFrame) -> pl.DataFrame:
    """Aggregate revenue by category on an eager DataFrame."""
    return (
        orders.group_by("category")
        .agg(pl.col("amount").sum().alias("revenue"))
        .sort("category")
    )


def lazy_join_collect(orders: pl.DataFrame, customers: pl.DataFrame) -> pl.DataFrame:
    """Join orders to customers lazily, aggregate, and collect in memory."""
    return (
        orders.lazy()
        .join(customers.lazy(), on="customer_id", how="inner")
        .group_by("region")
        .agg(pl.col("amount").sum().alias("revenue"))
        .sort("region")
        .collect()
    )


def streaming_query(orders: pl.DataFrame) -> pl.LazyFrame:
    """Build a lazy aggregation plan. Execution happens in ``collect_streaming``."""
    return (
        orders.lazy()
        .group_by("category")
        .agg(pl.col("amount").sum().alias("revenue"))
        .sort("category")
    )


def collect_streaming(lazy_frame: pl.LazyFrame) -> pl.DataFrame:
    """Collect with the streaming engine when this Polars build supports it.

    Current Polars accepts ``engine="streaming"``. Older releases accept
    ``streaming=True``. If the streaming engine rejects the plan, the same
    lazy query is collected in memory.
    """
    for kwargs in ({"engine": "streaming"}, {"streaming": True}):
        try:
            return lazy_frame.collect(**kwargs)
        except TypeError:
            continue
        except Exception:
            break
    return lazy_frame.collect()


def main() -> None:
    """Measure eager, lazy, and streaming Polars workloads."""
    orders, customers = sample_frames()
    eco = EcoTrace(
        region_code="DE",
        check_updates=False,
        run_label="polars-workload",
    )

    @eco.track
    def tracked_eager() -> pl.DataFrame:
        return eager_groupby(orders)

    @eco.track
    def tracked_lazy_join() -> pl.DataFrame:
        return lazy_join_collect(orders, customers)

    eager = tracked_eager()
    joined = tracked_lazy_join()

    query = streaming_query(orders)
    with eco.track_block("polars_streaming_collect"):
        streamed = collect_streaming(query)

    summary = eco.get_summary()
    print(f"Eager group-by rows : {eager.height}")
    print(f"Lazy join rows      : {joined.height}")
    print(f"Streaming rows      : {streamed.height}")
    print(f"Functions tracked   : {summary['functions_tracked']}")
    print(f"Carbon              : {summary['total_carbon_gco2']:.8f} gCO2")
    print(eager)
    print(joined)


if __name__ == "__main__":
    main()
