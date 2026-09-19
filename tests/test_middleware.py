import asyncio
import time
from unittest.mock import MagicMock, patch
import pytest

from ecotrace.middleware import fastapi as fastapi_mod
from ecotrace.middleware import flask as flask_mod


def test_fastapi_middleware_missing_dependency():
    with patch.object(fastapi_mod, "BaseHTTPMiddleware", object):
        with pytest.raises(ImportError):
            fastapi_mod.EcoTraceMiddleware(app=MagicMock())


def test_fastapi_middleware_dispatch_isolated():
    mock_eco = MagicMock()
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    mock_eco._get_avg_cpu_in_range.return_value = 10.0
    mock_eco._compute_carbon.return_value = 0.05
    mock_eco.cpu_info = {"tdp": 65.0}

    middleware = object.__new__(fastapi_mod.EcoTraceMiddleware)
    middleware.ecotrace = mock_eco
    middleware.log_to_csv = True

    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {}

    async def mock_call_next(req):
        return mock_response

    response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

    assert response.headers["X-Eco-Carbon-Emitted"] == "0.05000000g"
    assert "X-Eco-Duration" in response.headers
    mock_eco._accumulate_carbon.assert_called_once()


def test_fastapi_middleware_dispatch_exception_handled():
    mock_eco = MagicMock()
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    mock_eco._get_avg_cpu_in_range.side_effect = RuntimeError("error")

    middleware = object.__new__(fastapi_mod.EcoTraceMiddleware)
    middleware.ecotrace = mock_eco
    middleware.log_to_csv = False

    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {}

    async def mock_call_next(req):
        return mock_response

    response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))
    assert response == mock_response


def test_flask_middleware_missing_dependency():
    with patch.object(flask_mod, "request", None):
        middleware = flask_mod.EcoTraceFlask(app=None)
        with pytest.raises(ImportError):
            middleware.init_app(MagicMock())


def test_flask_middleware_lifecycle_isolated():
    mock_eco = MagicMock()
    mock_eco._get_avg_cpu_in_range.return_value = 12.0
    mock_eco._compute_carbon.return_value = 0.08
    mock_eco.cpu_info = {"tdp": 65.0}

    mock_app = MagicMock()
    mock_request = MagicMock()
    mock_request.environ = {}
    mock_request.path = "/test-route"

    with patch.object(flask_mod, "request", mock_request):
        middleware = flask_mod.EcoTraceFlask(
            app=mock_app,
            ecotrace_instance=mock_eco,
            log_to_csv=True,
        )
        assert mock_app.before_request.call_count == 1
        assert mock_app.after_request.call_count == 1

        middleware._before_request()
        assert "ecotrace_start_time" in mock_request.environ
        mock_eco._start_cpu_monitor.assert_called_once()

        mock_response = MagicMock()
        mock_response.headers = {}
        res = middleware._after_request(mock_response)

        assert res.headers["X-Eco-Carbon-Emitted"] == "0.08000000g"
        assert "X-Eco-Duration" in res.headers
        mock_eco._stop_cpu_monitor.assert_called_once()
        mock_eco._accumulate_carbon.assert_called_once()


def test_flask_middleware_after_request_exception_handled():
    mock_eco = MagicMock()
    mock_eco._get_avg_cpu_in_range.side_effect = ZeroDivisionError()
    mock_request = MagicMock()
    mock_request.environ = {"ecotrace_start_time": time.perf_counter()}

    with patch.object(flask_mod, "request", mock_request):
        middleware = flask_mod.EcoTraceFlask(app=None, ecotrace_instance=mock_eco)
        mock_response = MagicMock()
        mock_response.headers = {}
        res = middleware._after_request(mock_response)
        assert res == mock_response
