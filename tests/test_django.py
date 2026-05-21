import pytest
import time
from unittest.mock import MagicMock, patch
from ecotrace.core import EcoTrace
from ecotrace.middleware.django import EcoTraceDjangoMiddleware

@pytest.fixture
def mock_django_settings(monkeypatch):
    """Mock django.conf.settings"""
    mock_settings = MagicMock()
    mock_settings.ECOTRACE_INSTANCE = None
    mock_settings.ECOTRACE_LOG_CSV = False
    
    # We patch sys.modules to simulate Django being installed
    import sys
    import types
    django_module = types.ModuleType('django')
    django_conf = types.ModuleType('django.conf')
    django_conf.settings = mock_settings
    django_module.conf = django_conf
    
    monkeypatch.setitem(sys.modules, 'django', django_module)
    monkeypatch.setitem(sys.modules, 'django.conf', django_conf)
    return mock_settings

def test_django_middleware_sync_wsgi(mock_django_settings):
    """Test standard WSGI synchronous request flow."""
    mock_response = MagicMock()
    mock_response.__setitem__ = MagicMock()  # For dictionary-like header setting
    
    def dummy_get_response(request):
        time.sleep(0.01)
        return mock_response
        
    middleware = EcoTraceDjangoMiddleware(get_response=dummy_get_response)
    
    # Mock request
    request = MagicMock()
    request.META = {}
    
    # Execute middleware
    response = middleware(request)
    
    # Assert headers were injected
    assert response is mock_response
    assert "ecotrace_start_time" in request.META
    mock_response.__setitem__.assert_any_call("X-Eco-Carbon-Emitted", mock_response.__setitem__.call_args_list[0][0][1])
    mock_response.__setitem__.assert_any_call("X-Eco-Duration", mock_response.__setitem__.call_args_list[1][0][1])

import asyncio

def test_django_middleware_async_asgi(mock_django_settings):
    """Test ASGI asynchronous request flow."""
    mock_response = MagicMock()
    mock_response.__setitem__ = MagicMock()
    
    async def dummy_get_response_async(request):
        return mock_response
        
    with patch('ecotrace.middleware.django.iscoroutinefunction', return_value=True), \
         patch('ecotrace.middleware.django.markcoroutinefunction', MagicMock()):
        middleware = EcoTraceDjangoMiddleware(get_response=dummy_get_response_async)
    assert middleware.is_async is True
    
    # Mock request
    request = MagicMock()
    request.META = {}
    
    # Execute middleware asynchronously
    response = asyncio.run(middleware(request))
    
    assert response is mock_response
    assert "ecotrace_start_time" in request.META
    mock_response.__setitem__.assert_called()

def test_django_middleware_error_safety(mock_django_settings):
    """Test that measurement errors do not break the request cycle."""
    mock_response = MagicMock()
    def dummy_get_response(request):
        return mock_response
        
    middleware = EcoTraceDjangoMiddleware(get_response=dummy_get_response)
    
    request = MagicMock()
    request.META = {}
    
    # Break the ecotrace instance deliberately
    middleware.ecotrace._compute_carbon = MagicMock(side_effect=Exception("Forced fault"))
    
    # Execute middleware
    response = middleware(request)
    
    # Response should still be returned successfully despite the fault
    assert response is mock_response

