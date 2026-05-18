import pytest
import time
from unittest.mock import MagicMock, patch, call
from ecotrace.core import EcoTrace

def test_celery_plugin_initialization():
    """Verify Celery plugin aborts gracefully when celery signals are unavailable."""
    with patch('ecotrace.plugins.celery.task_prerun', None):
        from ecotrace.plugins.celery import EcoTraceCelery
        plugin = EcoTraceCelery()
        assert not hasattr(plugin, 'ecotrace')  # Aborts early

def _make_plugin(eco, log_to_csv=True):
    """Helper that constructs EcoTraceCelery with all signals mocked."""
    mock_prerun = MagicMock()
    mock_postrun = MagicMock()
    mock_retry = MagicMock()
    mock_revoked = MagicMock()

    with patch('ecotrace.plugins.celery.task_prerun', mock_prerun), \
         patch('ecotrace.plugins.celery.task_postrun', mock_postrun), \
         patch('ecotrace.plugins.celery.task_retry', mock_retry), \
         patch('ecotrace.plugins.celery.task_revoked', mock_revoked):
        from ecotrace.plugins.celery import EcoTraceCelery
        plugin = EcoTraceCelery(ecotrace_instance=eco, log_to_csv=log_to_csv)

    return plugin

def test_celery_task_lifecycle():
    """Test the full prerun -> postrun lifecycle for a successful task."""
    eco = EcoTrace(quiet=True, check_updates=False)
    eco._accumulate_carbon = MagicMock()

    plugin = _make_plugin(eco)

    mock_task = MagicMock()
    mock_task.name = "my_worker_task"

    # Simulate task start
    plugin._on_task_prerun(task_id="1234-abcd", task=mock_task)
    assert "1234-abcd" in plugin._task_state
    assert eco._cpu_monitor_ref_count == 1

    time.sleep(0.01)

    # Simulate task end
    plugin._on_task_postrun(task_id="1234-abcd", task=mock_task)
    assert "1234-abcd" not in plugin._task_state
    assert eco._cpu_monitor_ref_count == 0
    eco._accumulate_carbon.assert_called_once()
    assert eco._accumulate_carbon.call_args[0][1] == "Celery: my_worker_task"

def test_celery_task_retry_lifecycle():
    """Test that retry finalizes attempt 1 independently, preventing double-counting."""
    eco = EcoTrace(quiet=True, check_updates=False)
    eco._accumulate_carbon = MagicMock()

    plugin = _make_plugin(eco)

    mock_task = MagicMock()
    mock_task.name = "flaky_task"

    # Attempt 1: Start
    plugin._on_task_prerun(task_id="retry-111", task=mock_task)

    # Attempt 1: Retry exception
    mock_request = MagicMock()
    mock_request.id = "retry-111"
    mock_request.task = "flaky_task"
    plugin._on_task_retry(request=mock_request, reason="Connection Error", einfo=None)

    assert "retry-111" not in plugin._task_state
    assert eco._accumulate_carbon.call_count == 1

    # Attempt 2: Start + succeed
    plugin._on_task_prerun(task_id="retry-111", task=mock_task)
    plugin._on_task_postrun(task_id="retry-111", task=mock_task)
    assert eco._accumulate_carbon.call_count == 2

# /* --- Hybrid End of File / Dosya Sonu --- */ #
