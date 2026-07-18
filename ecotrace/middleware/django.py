import time
import logging
from typing import Optional

logger = logging.getLogger("ecotrace.middleware.django")

try:
    import importlib
    asgiref_sync = importlib.import_module("asgiref.sync")
    iscoroutinefunction = asgiref_sync.iscoroutinefunction
    markcoroutinefunction = asgiref_sync.markcoroutinefunction
except ImportError:
    iscoroutinefunction = None
    markcoroutinefunction = None

from ecotrace.core import EcoTrace

class EcoTraceDjangoMiddleware:
    """Django middleware for tracking carbon emissions per request.
    
    Supports both WSGI (synchronous) and ASGI (asynchronous) views seamlessly.
    Injects 'X-Eco-Carbon-Emitted' and 'X-Eco-Duration' headers into every response.
    
    Can be configured via Django settings:
        ECOTRACE_INSTANCE: An already initialized EcoTrace instance.
        ECOTRACE_LOG_CSV: Boolean to enable CSV logging of requests.
    """
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        if iscoroutinefunction is None:
            msg = "EcoTraceDjangoMiddleware requires 'django' (which includes asgiref). Run: pip install ecotrace[web]"
            logger.error(msg)
            
        self.get_response = get_response
        self.is_async = False
        if iscoroutinefunction is not None:
            self.is_async = iscoroutinefunction(self.get_response)
        
        if self.is_async and markcoroutinefunction is not None:
            markcoroutinefunction(self)
            
        # Try to load configuration from Django settings safely
        try:
            import importlib
            django_conf = importlib.import_module("django.conf")
            settings = django_conf.settings
            ecotrace_instance = getattr(settings, 'ECOTRACE_INSTANCE', None)
            self.log_to_csv = getattr(settings, 'ECOTRACE_LOG_CSV', False)
        except (ImportError, AttributeError):
            ecotrace_instance = None
            self.log_to_csv = False

        self.ecotrace = ecotrace_instance or EcoTrace(quiet=True, check_updates=False)

    def __call__(self, request):
        if self.is_async:
            return self.__acall__(request)
            
        # Synchronous WSGI flow
        request.META['ecotrace_start_time'] = time.perf_counter()
        self.ecotrace._start_cpu_monitor()
        response = None
        try:
            response = self.get_response(request)
        finally:
            self._finalize_measurement(request, response)
            
        return response

    async def __acall__(self, request):
        # Asynchronous ASGI flow
        request.META['ecotrace_start_time'] = time.perf_counter()
        self.ecotrace._start_cpu_monitor()
        response = None
        try:
            response = await self.get_response(request)
        finally:
            self._finalize_measurement(request, response)
            
        return response

    def _finalize_measurement(self, request, response):
        """Resolves carbon metrics and injects response headers."""
        self.ecotrace._stop_cpu_monitor()
        
        start_time = request.META.get('ecotrace_start_time')
        if not start_time:
            return
            
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        try:
            avg_cpu = self.ecotrace._get_avg_cpu_in_range(start_time, end_time)
            carbon_emitted = self.ecotrace._compute_carbon(
                self.ecotrace.cpu_info['tdp'], avg_cpu, duration
            )
            
            if response:
                response["X-Eco-Carbon-Emitted"] = f"{carbon_emitted:.8f}g"
                response["X-Eco-Duration"] = f"{duration:.4f}s"
            
            if self.log_to_csv:
                func_name = f"{request.method} {request.path}"
                self.ecotrace._accumulate_carbon(carbon_emitted, func_name, duration, avg_cpu)
                
        except Exception as e:
            # Objective: Never crash the main request cycle if measurement fails
            logger.debug(f"EcoTrace Django measurement failed: {e}")

# Backward-compatible alias (renamed in v1.1.2, alias kept for migration)
EcoTraceMiddleware = EcoTraceDjangoMiddleware

# /* --- Hybrid End of File / Dosya Sonu --- */ #
# // EcoTrace Django Middleware Integration // #
