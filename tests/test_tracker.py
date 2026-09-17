import asyncio
import os
import pytest
from ecotrace import EmissionsTracker, OfflineEmissionsTracker, track_emissions


def test_tracker_start_stop():
    tracker = EmissionsTracker(project_name="test_start_stop", quiet=True)
    tracker.start()
    total = sum(i * i for i in range(100000))
    emissions = tracker.stop()

    assert total > 0
    assert isinstance(emissions, float)
    assert emissions >= 0.0
    assert tracker.duration_seconds > 0.0
    assert tracker.final_emissions == emissions
    assert tracker.final_emissions_g >= 0.0


def test_tracker_context_manager():
    with EmissionsTracker(project_name="test_context", quiet=True) as tracker:
        res = [x * 2 for x in range(50000)]

    assert len(res) == 50000
    assert isinstance(tracker.final_emissions, float)
    assert tracker.duration_seconds > 0.0


def test_tracker_writes_to_ecotrace_log_csv():
    csv_file = "ecotrace_log.csv"
    initial_size = os.path.getsize(csv_file) if os.path.isfile(csv_file) else 0

    tracker = EmissionsTracker(project_name="test_csv_logging", quiet=True)
    tracker.start()
    _ = [x for x in range(20000)]
    tracker.stop()

    assert os.path.isfile(csv_file)
    assert os.path.getsize(csv_file) > initial_size


def test_tracker_custom_output_file(tmp_path):
    out_dir = str(tmp_path)
    out_file = "custom_emissions.csv"
    tracker = EmissionsTracker(
        project_name="test_custom_output",
        output_dir=out_dir,
        output_file=out_file,
        quiet=True,
    )
    tracker.start()
    _ = sum(range(10000))
    tracker.stop()

    full_path = os.path.join(out_dir, out_file)
    assert os.path.isfile(full_path)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "test_custom_output" in content


def test_track_emissions_decorator_sync():
    @track_emissions(project_name="test_sync_decorator")
    def compute(a, b):
        return a + b

    result = compute(10, 20)
    assert result == 30


def test_track_emissions_decorator_async():
    @track_emissions(project_name="test_async_decorator")
    async def async_compute(val):
        await asyncio.sleep(0.01)
        return val * 3

    result = asyncio.run(async_compute(7))
    assert result == 21


def test_track_emissions_no_args():
    @track_emissions
    def bare_func():
        return "ok"

    assert bare_func() == "ok"


def test_offline_emissions_tracker():
    tracker = OfflineEmissionsTracker(country_iso_code="TR", project_name="test_offline")
    tracker.start()
    _ = [i for i in range(10000)]
    emissions = tracker.stop()

    assert isinstance(emissions, float)
    assert emissions >= 0.0
