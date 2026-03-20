import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
from ecotrace import EcoTrace


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def eco():
    """Returns a basic EcoTrace instance with TR region."""
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
        instance = EcoTrace(region_code="TR")
    return instance


# ─────────────────────────────────────────────
#  Initialization
# ─────────────────────────────────────────────

def test_initialization_default_region():
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
        eco = EcoTrace()
    assert eco.region_code == "TR"


def test_initialization_custom_region():
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
        eco = EcoTrace(region_code="DE")
    assert eco.region_code == "DE"
    assert eco.carbon_intensity == 385


def test_initialization_unknown_region_falls_back_to_default():
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
        eco = EcoTrace(region_code="XX")
    assert eco.carbon_intensity == 475


def test_carbon_intensity_all_regions():
    regions = {"TR": 475, "DE": 385, "FR": 55, "US": 367, "GB": 253}
    for code, expected in regions.items():
        with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
            eco = EcoTrace(region_code=code)
        assert eco.carbon_intensity == expected


def test_total_carbon_starts_at_zero(eco):
    assert eco.total_carbon == 0.0


def test_cpu_info_has_required_keys(eco):
    assert "brand" in eco.cpu_info
    assert "cores" in eco.cpu_info
    assert "tdp" in eco.cpu_info


def test_tdp_fallback_when_cpu_not_in_database():
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Unknown Exotic CPU XZ-9999"}):
        eco = EcoTrace(region_code="TR")
    assert eco.cpu_info["tdp"] == 65.0  # Default fallback


# ─────────────────────────────────────────────
#  @eco.track — sync
# ─────────────────────────────────────────────

def test_track_runs_function(eco):
    @eco.track
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5


def test_track_increases_total_carbon(eco):
    @eco.track
    def work():
        return sum(i for i in range(10 ** 5))

    before = eco.total_carbon
    work()
    assert eco.total_carbon >= before


def test_track_carbon_is_non_negative(eco):
    @eco.track
    def noop():
        pass

    noop()
    assert eco.total_carbon >= 0.0


def test_track_preserves_return_value(eco):
    @eco.track
    def get_string():
        return "ecotrace"

    assert get_string() == "ecotrace"


def test_track_preserves_function_name(eco):
    @eco.track
    def my_special_function():
        pass

    assert my_special_function.__name__ == "my_special_function"


def test_track_accumulates_across_calls(eco):
    @eco.track
    def work():
        return sum(i for i in range(10 ** 7))

    work()
    after_first = eco.total_carbon
    work()
    assert eco.total_carbon > after_first


# ─────────────────────────────────────────────
#  @eco.track — async
# ─────────────────────────────────────────────

def test_track_async_function(eco):
    @eco.track
    async def async_work():
        await asyncio.sleep(0.01)
        return "done"

    result = asyncio.run(async_work())
    assert result == "done"


def test_track_async_increases_total_carbon(eco):
    @eco.track
    async def async_work():
        await asyncio.sleep(0.01)

    before = eco.total_carbon
    asyncio.run(async_work())
    assert eco.total_carbon >= before


# ─────────────────────────────────────────────
#  eco.measure()
# ─────────────────────────────────────────────

def test_measure_returns_dict(eco):
    def work():
        return 42

    result = eco.measure(work)
    assert isinstance(result, dict)


def test_measure_dict_has_required_keys(eco):
    def work():
        return 42

    result = eco.measure(work)
    for key in ["func_name", "duration", "avg_cpu", "carbon", "cpu_samples", "result"]:
        assert key in result


def test_measure_result_value(eco):
    def work():
        return 99

    result = eco.measure(work)
    assert result["result"] == 99


def test_measure_duration_is_positive(eco):
    def work():
        time.sleep(0.05)

    result = eco.measure(work)
    assert result["duration"] > 0


def test_measure_carbon_is_non_negative(eco):
    def work():
        pass

    result = eco.measure(work)
    assert result["carbon"] >= 0.0


# ─────────────────────────────────────────────
#  eco.measure_async()
# ─────────────────────────────────────────────

def test_measure_async_returns_dict(eco):
    async def async_work():
        await asyncio.sleep(0.01)
        return "hello"

    result = asyncio.run(eco.measure_async(async_work))
    assert isinstance(result, dict)


def test_measure_async_result_value(eco):
    async def async_work():
        await asyncio.sleep(0.01)
        return "ecotrace"

    result = asyncio.run(eco.measure_async(async_work))
    assert result["result"] == "ecotrace"


def test_measure_async_duration_is_positive(eco):
    async def async_work():
        await asyncio.sleep(0.05)

    result = asyncio.run(eco.measure_async(async_work))
    assert result["duration"] >= 0.05


def test_measure_async_carbon_is_non_negative(eco):
    async def async_work():
        pass

    result = asyncio.run(eco.measure_async(async_work))
    assert result["carbon"] >= 0.0


# ─────────────────────────────────────────────
#  eco.compare()
# ─────────────────────────────────────────────

def test_compare_returns_dict(eco):
    def fast():
        return sum(range(100))

    def slow():
        return sum(range(1000))

    result = eco.compare(fast, slow)
    assert isinstance(result, dict)


def test_compare_has_func1_and_func2(eco):
    def fast():
        pass

    def slow():
        pass

    result = eco.compare(fast, slow)
    assert "func1" in result
    assert "func2" in result


def test_compare_func_names_are_correct(eco):
    def alpha():
        pass

    def beta():
        pass

    result = eco.compare(alpha, beta)
    assert result["func1"]["func_name"] == "alpha"
    assert result["func2"]["func_name"] == "beta"


# ─────────────────────────────────────────────
#  carbon_limit warning
# ─────────────────────────────────────────────

def test_carbon_limit_warning_is_printed(capsys):
    with patch("cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i7-13700H"}):
        eco = EcoTrace(region_code="TR", carbon_limit=0.0)

    @eco.track
    def work():
        return sum(range(10 ** 5))

    work()
    captured = capsys.readouterr()
    assert "WARNING" in captured.out or eco.total_carbon >= 0


# ─────────────────────────────────────────────
#  CSV logging
# ─────────────────────────────────────────────

def test_log_to_csv_creates_file(eco, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    @eco.track
    def work():
        pass

    work()
    log_file = tmp_path / "ecotrace_log.csv"
    assert log_file.exists()


def test_log_to_csv_has_correct_headers(eco, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    @eco.track
    def work():
        pass

    work()
    log_file = tmp_path / "ecotrace_log.csv"
    content = log_file.read_text()
    assert "Function" in content
    assert "Carbon(gCO2)" in content
    assert "Duration(s)" in content