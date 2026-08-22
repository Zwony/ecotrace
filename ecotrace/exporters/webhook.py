import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("ecotrace.exporters.webhook")

try:
    import requests  # type: ignore
except ImportError:
    requests = None

from ecotrace.core import EcoTrace

class WebhookExporter:
    """Webhook metrics exporter for EcoTrace carbon emissions.
    
    Sends a POST request to a configurable webhook URL whenever a measurement completes.
    
    Args:
        ecotrace_instance: The initialized EcoTrace core instance to attach to.
        url: The webhook HTTP/HTTPS endpoint.
        headers: Optional dict of extra HTTP headers (e.g. for auth/tokens).
    """
    
    def __init__(
        self, 
        ecotrace_instance: EcoTrace, 
        url: str,
        headers: Optional[Dict[str, str]] = None
    ):
        if requests is None:
            msg = "WebhookExporter requires 'requests'. Please install requests."
            logger.error(msg)
            self.url = None
            return
            
        self.ecotrace = ecotrace_instance
        self.url = url
        self.headers = headers or {}
        
        # Attach self to the EcoTrace engine
        self.ecotrace.add_exporter(self)
        logger.info(f"Webhook Exporter attached to EcoTrace (url: {self.url}).")

    def export(self, carbon_emitted: float, func_name: str, duration: float, region: str, run_id: Optional[str] = None, run_label: Optional[str] = None, **kwargs):
        """Called synchronously by EcoTrace whenever a measurement completes.
        
        Args:
            carbon_emitted: The measured footprint in gCO2.
            func_name: The name of the function or block that was tracked.
            duration: The execution time in seconds.
            region: The grid intensity region code used (e.g., 'US', 'DE').
        """
        if not self.url or requests is None:
            return
            
        payload = {
            "function": func_name,
            "carbon_gco2": carbon_emitted,
            "duration_s": duration,
            "region": region,
            "run_id": getattr(self.ecotrace, "_run_id", ""),
            "run_label": getattr(self.ecotrace, "_run_label", "")
        }
        
        try:
            req_headers = {"Content-Type": "application/json"}
            req_headers.update(self.headers)
            response = requests.post(self.url, json=payload, headers=req_headers, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.debug(f"Failed to send webhook metric: {e}")
