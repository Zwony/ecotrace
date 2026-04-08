import time
import logging
from typing import Optional

# Diagnostic logging facility for middleware-level events.
logger = logging.getLogger("ecotrace.middleware")

try:
    from flask import request, Response  # type: ignore
except ImportError:
    request = None
    Response = None

from ecotrace.core import EcoTrace

class EcoTraceFlask:
    """Flask extension for tracking carbon emissions per request.
    
    Injects 'X-Eco-Carbon-Emitted' and 'X-Eco-Duration' headers into every response.
    
    Args:
        app: The Flask application.
        ecotrace_instance: Optional initialized EcoTrace instance. If not provided,
            it creates one quietly.
        log_to_csv: Whether to log each request to the ecotrace_log.csv. Default False.
    """
    def __init__(self, app=None, ecotrace_instance: Optional[EcoTrace] = None, log_to_csv: bool = False):
        if request is None:
            msg = "EcoTraceFlask requires 'flask' to be installed. Run: pip install ecotrace[web] or pip install flask"
            logger.error(msg)
            # We don't raise ImportError here to allow the extension to be initialized 
            # if flask is missing locally (e.g. during static analysis), but it will 
            # fail on init_app.
        
        self.ecotrace = ecotrace_instance or EcoTrace(quiet=True, check_updates=False)
        self.log_to_csv = log_to_csv
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        """Initializes the extension with the Flask app."""
        if request is None:
             raise ImportError("flask is required to use EcoTraceFlask.")

        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        """Pre-request instrumentation hook to initialize monitoring state."""
        request.environ['ecotrace_start_time'] = time.perf_counter()
        self.ecotrace._start_cpu_monitor()

    def _after_request(self, response: Response) -> Response:
        """Post-request teardown hook to snapshot and resolve carbon metrics."""
        self.ecotrace._stop_cpu_monitor()
        
        start_time = request.environ.get('ecotrace_start_time')
        if not start_time:
            return response
            
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        try:
            avg_cpu = self.ecotrace._get_avg_cpu_in_range(start_time, end_time)
            carbon_emitted = self.ecotrace._compute_carbon(
                self.ecotrace.cpu_info['tdp'], avg_cpu, duration
            )
            
            # Inject headers for client-side visibility
            response.headers["X-Eco-Carbon-Emitted"] = f"{carbon_emitted:.8f}g"
            response.headers["X-Eco-Duration"] = f"{duration:.4f}s"
            
            if self.log_to_csv:
                func_name = f"{request.method} {request.path}"
                self.ecotrace._accumulate_carbon(carbon_emitted, func_name, duration, avg_cpu)
                
        except Exception as e:
            # Objective: Never crash the main request cycle if measurement fails
            logger.debug(f"EcoTrace measurement failed: {e}")
            
        return response
