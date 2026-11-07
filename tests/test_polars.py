import pytest

from ecotrace import EcoTrace


@pytest.fixture
def isolated_cwd(tmp_path, monkeypatch):
    # EcoTrace.track / track_block always write their CSV audit log
    # relative to the current working directory, so isolate it per test.
    monkeypatch.chdir(tmp_path)


def test_tracked_eager_groupby_matches_untracked(isolated_cwd):
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"category": [1, 1, 2, 2, 3], "amount": [10.0, 20.0, 5.0, 5.0, 100.0]})

    def eager_groupby(frame):
        return frame.group_by("category").agg(pl.col("amount").sum().alias("total")).sort("category")

    expected = eager_groupby(df)

    eco = EcoTrace(region_code="GLOBAL", check_updates=False, quiet=True)

    @eco.track
    def tracked_groupby(frame):
        return eager_groupby(frame)

    actual = tracked_groupby(df)

    assert isinstance(actual, type(expected))
    assert actual.sort("category").equals(expected)


def test_tracked_lazy_pipeline_collect_inside_scope(isolated_cwd):
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({
        "category": [1, 1, 2, 2, 3],
        "country": ["US", "DE", "US", "GB", "FR"],
        "amount": [10.0, 20.0, 5.0, 5.0, 100.0],
    })

    def lazy_pipeline(frame):
        query = (
            frame.lazy()
            .filter(pl.col("country").is_in(["US", "DE", "GB"]))
            .group_by("category")
            .agg(pl.col("amount").sum().alias("total"))
            .sort("category")
        )
        return query.collect()

    expected = lazy_pipeline(df)

    eco = EcoTrace(region_code="GLOBAL", check_updates=False, quiet=True)

    with eco.track_block("lazy_pipeline_test"):
        actual = lazy_pipeline(df)

    assert isinstance(actual, pl.DataFrame)
    assert actual.equals(expected)


def test_track_block_produces_measurement_record(isolated_cwd):
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"category": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})

    eco = EcoTrace(region_code="GLOBAL", check_updates=False, quiet=True)

    with eco.track_block("polars_block_test"):
        df.group_by("category").agg(pl.col("amount").sum())

    assert eco._tracked_functions_count == 1
    assert eco.total_carbon >= 0.0


def test_track_decorator_produces_measurement_record(isolated_cwd):
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"category": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})

    eco = EcoTrace(region_code="GLOBAL", check_updates=False, quiet=True)

    @eco.track
    def tracked(frame):
        return frame.group_by("category").agg(pl.col("amount").sum())

    tracked(df)

    assert eco._tracked_functions_count == 1
    assert eco.total_carbon >= 0.0
