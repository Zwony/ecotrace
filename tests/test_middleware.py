import pytest
from unittest.mock import MagicMock, AsyncMock, patch

try:
    from starlette.requests import Request
    from starlette.responses import Response
    from ecotrace.middleware.fastapi import EcoTraceMiddleware
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from flask import Flask, request, make_response
    from ecotrace.middleware.flask import EcoTraceFlask
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


@pytest.mark.skipif(not HAS_FASTAPI, reason="Starlette/FastAPI not installed")
def test_fastapi_middleware():
    import asyncio
    mock_app = MagicMock()
    mock_eco = MagicMock()
    # Mock the context managers
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    
    mock_eco._get_avg_cpu_in_range.return_value = 10.0
    mock_eco._compute_carbon.return_value = 0.05
    mock_eco.cpu_info = {"tdp": 65.0}

    middleware = EcoTraceMiddleware(app=mock_app, ecotrace_instance=mock_eco, log_to_csv=False)
    
    # Mock Request and Response
    mock_request = MagicMock(spec=Request)
    mock_response = MagicMock(spec=Response)
    mock_response.headers = {}
    
    async def mock_call_next(req):
        return mock_response
        
    response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))
    
    assert "X-Eco-Carbon-Emitted" in response.headers
    assert "X-Eco-Duration" in response.headers
    assert response.headers["X-Eco-Carbon-Emitted"] == "0.05000000g"


@pytest.mark.skipif(not HAS_FLASK, reason="Flask not installed")
def test_flask_middleware():
    app = Flask(__name__)
    mock_eco = MagicMock()
    mock_eco.cpu_monitor.return_value.__enter__ = MagicMock()
    mock_eco.cpu_monitor.return_value.__exit__ = MagicMock()
    
    mock_eco._get_avg_cpu_in_range.return_value = 15.0
    mock_eco._compute_carbon.return_value = 0.1
    mock_eco.cpu_info = {"tdp": 65.0}
    
    # Initialize middleware
    middleware = EcoTraceFlask(app=app, ecotrace_instance=mock_eco, log_to_csv=False)
    
    @app.route("/test")
    def test_route():
        return "OK"
        
    with app.test_client() as client:
        response = client.get("/test")
        
    assert "X-Eco-Carbon-Emitted" in response.headers
    assert "X-Eco-Duration" in response.headers
    assert response.headers["X-Eco-Carbon-Emitted"] == "0.10000000g"
