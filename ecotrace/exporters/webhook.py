import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ecotrace.exporters.webhook")

try:
    import requests  # type: ignore
except ImportError:
    requests = None

from ecotrace.core import EcoTrace

WEBHOOK_FORMATS = ("json", "discord")
DISCORD_COLOR_GREEN = 0x2ECC71
DISCORD_COLOR_RED = 0xE74C3C

class WebhookExporter:
    """Webhook metrics exporter for EcoTrace carbon emissions.
    
    Sends a POST request to a configurable webhook URL whenever a measurement completes.
    
    Args:
        ecotrace_instance: The initialized EcoTrace core instance to attach to.
        url: The webhook HTTP/HTTPS endpoint.
        headers: Optional dict of extra HTTP headers (e.g. for auth/tokens).
        format: Payload format. "json" (default) sends the raw metrics dict. "discord"
            sends a Discord embed with the function name, gCO2 and duration, green
            below the EcoTrace instance's carbon_limit (or when none is set) and red at
            or above it. An unknown value logs a warning and falls back to "json".
    """
    
    def __init__(
        self, 
        ecotrace_instance: EcoTrace, 
        url: str,
        headers: Optional[Dict[str, str]] = None,
        format: str = "json"
    ):
        if requests is None:
            msg = "WebhookExporter requires 'requests'. Please install requests."
            logger.error(msg)
            self.url = None
            return
            
        self.ecotrace = ecotrace_instance
        self.url = url
        self.headers = headers or {}
        if format not in WEBHOOK_FORMATS:
            logger.warning(f"Invalid format={format!r}, defaulting to 'json'.")
            format = "json"
        self.format = format
        
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
        if self.format == "discord":
            payload = self._discord_payload(carbon_emitted, func_name, duration)
        
        try:
            req_headers = {"Content-Type": "application/json"}
            req_headers.update(self.headers)
            response = requests.post(self.url, json=payload, headers=req_headers, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.debug(f"Failed to send webhook metric: {e}")

    def _discord_payload(self, carbon_emitted: float, func_name: str, duration: float) -> Dict[str, Any]:
        """Builds a Discord embed, green below carbon_limit (or without one) and red at or above it."""
        limit = getattr(self.ecotrace, "carbon_limit", None)
        over_limit = isinstance(limit, (int, float)) and carbon_emitted >= limit
        return {
            "embeds": [{
                "title": f"EcoTrace: {func_name}",
                "color": DISCORD_COLOR_RED if over_limit else DISCORD_COLOR_GREEN,
                "fields": [
                    {"name": "Carbon", "value": f"{carbon_emitted:.6f} gCO2", "inline": True},
                    {"name": "Duration", "value": f"{duration:.2f} s", "inline": True},
                ],
            }]
        }
