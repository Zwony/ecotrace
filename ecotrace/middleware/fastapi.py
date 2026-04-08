import time
import logging
from typing import Optional

# Setup local logger for middleware-specific warnings
logger = logging.getLogger("ecotrace.middleware")

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError:
    BaseHTTPMiddleware = object  # Avoid failing import if not installed
    Request = None
    Response = None

from ecotrace.core import EcoTrace

class EcoTraceMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware for tracking carbon emissions per request.
    
    Injects 'X-Eco-Carbon-Emitted' and 'X-Eco-Duration' headers into every response.
    
    Args:
        app: The ASGI application.
        ecotrace_instance: Optional initialized EcoTrace instance. If not provided,
            it creates one quietly.
        log_to_csv: Whether to log each request to the ecotrace_log.csv. Default False.
    """
    def __init__(self, app, ecotrace_instance: Optional[EcoTrace] = None, log_to_csv: bool = False):
        if BaseHTTPMiddleware is object:
            msg = "EcoTraceMiddleware requires 'starlette' to be installed. Run: pip install ecotrace[web] or pip install starlette"
            logger.error(msg)
            raise ImportError(msg)
            
        super().__init__(app)
        self.ecotrace = ecotrace_instance or EcoTrace(quiet=True, check_updates=False)
        self.log_to_csv = log_to_csv

    async def dispatch(self, request: Request, call_next) -> Response:
        """Instruments a single HTTP request for carbon monitoring."""
        start_time = time.perf_counter()
        
        # Continuous background sampling starts here
        with self.ecotrace.cpu_monitor():
            response = await call_next(request)
            
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Calculate carbon emissions using hardware TDP and average utilization
        try:
            avg_cpu = self.ecotrace._get_avg_cpu_in_range(start_time, end_time)
            carbon_emitted = self.ecotrace._compute_carbon(
                self.ecotrace.cpu_info['tdp'], avg_cpu, duration
            )
            
            # Inject headers for client-side visibility
            response.headers["X-Eco-Carbon-Emitted"] = f"{carbon_emitted:.8f}g"
            response.headers["X-Eco-Duration"] = f"{duration:.4f}s"
            
            if self.log_to_csv:
                func_name = f"{request.method} {request.url.path}"
                self.ecotrace._accumulate_carbon(carbon_emitted, func_name, duration, avg_cpu)
                
        except Exception as e:
            # Objective: Never crash the main request cycle if measurement fails
            logger.debug(f"EcoTrace measurement failed: {e}")
            
        return response
