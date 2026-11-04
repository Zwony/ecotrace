"""Integration tests for @eco.track on functions that return Polars objects."""

import pytest

pl = pytest.importorskip("polars")

from ecotrace import EcoTrace


@pytest.fixture
def eco():
    return EcoTrace(
        region_code="US",
        check_updates=False,
        quiet=True,
        session_summary=False,
    )


def _orders():
    return pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4],
            "customer_id": [10, 11, 10, 12],
            "category": ["books", "books", "games", "games"],
            "amount": [12.5, 8.0, 40.0, 15.0],
        }
    )


def _customers():
    return pl.DataFrame(
        {
            "customer_id": [10, 11, 12],
            "region": ["EU", "US", "EU"],
        }
    )


def test_track_returns_polars_dataframe(eco):
    """@eco.track must return the DataFrame, not the measurement dict."""

    @eco.track
    def aggregate(frame):
        return (
            frame.group_by("category")
            .agg(pl.col("amount").sum().alias("revenue"))
            .sort("category")
        )

    result = aggregate(_orders())

    assert isinstance(result, pl.DataFrame)
    assert not isinstance(result, dict)
    totals = dict(zip(result["category"].to_list(), result["revenue"].to_list()))
    assert totals == {"books": 20.5, "games": 55.0}
    assert eco.get_summary()["functions_tracked"] == 1


def test_track_returns_polars_lazyframe(eco):
    """A LazyFrame returned by a tracked function stays executable."""

    @eco.track
    def build_plan(frame):
        return frame.lazy().filter(pl.col("amount") > 10.0).select("order_id", "amount")

    lazy = build_plan(_orders())

    assert isinstance(lazy, pl.LazyFrame)
    collected = lazy.collect()
    assert collected["order_id"].to_list() == [1, 3, 4]
    assert eco.get_summary()["functions_tracked"] == 1


def test_track_returns_collected_join(eco):
    """Tracking wraps lazy join + collect and still returns a DataFrame."""

    @eco.track
    def join_and_collect(orders, customers):
        return (
            orders.lazy()
            .join(customers.lazy(), on="customer_id", how="inner")
            .group_by("region")
            .agg(pl.col("amount").sum().alias("revenue"))
            .sort("region")
            .collect()
        )

    result = join_and_collect(_orders(), _customers())

    assert isinstance(result, pl.DataFrame)
    totals = dict(zip(result["region"].to_list(), result["revenue"].to_list()))
    assert totals == {"EU": 67.5, "US": 8.0}
    assert eco.get_summary()["functions_tracked"] == 1


def test_track_block_around_lazy_collect(eco):
    """Context-manager tracking leaves the collected DataFrame intact."""
    query = (
        _orders()
        .lazy()
        .group_by("category")
        .agg(pl.col("amount").sum().alias("revenue"))
        .sort("category")
    )

    with eco.track_block("polars_collect"):
        result = query.collect()

    assert isinstance(result, pl.DataFrame)
    assert result["category"].to_list() == ["books", "games"]
    assert eco.get_summary()["functions_tracked"] == 1
