import threading
from unittest.mock import MagicMock, patch
import pytest

from ecotrace.plugins import pytest_plugin


def test_pytest_addoption():
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group
    pytest_plugin.pytest_addoption(parser)
    parser.getgroup.assert_called_once_with("ecotrace")
    assert group.addoption.call_count == 1


def test_pytest_configure_flag_set():
    config = MagicMock()
    config.getoption.side_effect = lambda flag: flag == "--ecotrace"
    with patch("ecotrace.plugins.pytest_plugin.EcoTrace") as mock_eco:
        pytest_plugin.pytest_configure(config)
        mock_eco.assert_called_once_with(quiet=True, check_updates=False)
        assert pytest_plugin.ecotrace_instance is not None


def test_pytest_configure_flag_unset():
    config = MagicMock()
    config.getoption.return_value = False
    pytest_plugin.ecotrace_instance = None
    pytest_plugin.pytest_configure(config)
    assert pytest_plugin.ecotrace_instance is None


def test_pytest_runtest_protocol_inactive():
    pytest_plugin.ecotrace_instance = None
    item = MagicMock()
    generator = pytest_plugin.pytest_runtest_protocol(item, None)
    next(generator)
    with pytest.raises(StopIteration):
        next(generator)


def test_pytest_runtest_protocol_active():
    mock_eco = MagicMock()
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    mock_eco._get_avg_cpu_in_range.return_value = 25.0
    mock_eco._compute_carbon.return_value = 0.042
    mock_eco.cpu_info = {"tdp": 65.0}

    pytest_plugin.ecotrace_instance = mock_eco
    pytest_plugin.test_emissions.clear()

    item = MagicMock()
    item.nodeid = "tests/test_sample.py::test_case"
    item.name = "test_case"

    generator = pytest_plugin.pytest_runtest_protocol(item, None)
    next(generator)
    with pytest.raises(StopIteration):
        next(generator)

    assert "tests/test_sample.py::test_case" in pytest_plugin.test_emissions
    assert pytest_plugin.test_emissions["tests/test_sample.py::test_case"]["carbon"] == 0.042
    mock_eco._accumulate_carbon.assert_called_once()


def test_pytest_runtest_protocol_exception_handled():
    mock_eco = MagicMock()
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    mock_eco._get_avg_cpu_in_range.side_effect = RuntimeError("CPU range error")

    pytest_plugin.ecotrace_instance = mock_eco
    item = MagicMock()
    item.nodeid = "tests/test_err.py::test_fail"

    generator = pytest_plugin.pytest_runtest_protocol(item, None)
    next(generator)
    with pytest.raises(StopIteration):
        next(generator)


def test_pytest_terminal_summary_disabled():
    reporter = MagicMock()
    config = MagicMock()
    config.getoption.return_value = False
    pytest_plugin.test_emissions = {"test": {"carbon": 0.1, "duration": 1.0, "avg_cpu": 20.0}}
    pytest_plugin.pytest_terminal_summary(reporter, 0, config)
    reporter.section.assert_not_called()


def test_pytest_terminal_summary_active():
    reporter = MagicMock()
    config = MagicMock()
    config.getoption.return_value = True
    pytest_plugin.test_emissions = {
        "test_a": {"carbon": 0.05, "duration": 1.2, "avg_cpu": 30.0},
        "test_b": {"carbon": 0.15, "duration": 2.5, "avg_cpu": 50.0},
    }
    pytest_plugin.pytest_terminal_summary(reporter, 0, config)
    reporter.section.assert_called_once()
    assert reporter.write_line.call_count >= 5
