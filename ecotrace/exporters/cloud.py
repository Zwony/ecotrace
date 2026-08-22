import os
import time
from typing import Optional
import requests
from ..logger import logger


class CloudExporter:
    """Telemetry exporter for streaming carbon metrics directly to the EcoTrace Hosted Dashboard.

    Sends telemetry payloads matching the FastAPI ``MeasurementIn`` schema to the EcoTrace
    ingestion endpoint using the user's private ``ingestion_key`` (``eco_usr_...``).

    Args:
        api_key (str): User's private ingestion key (e.g. ``eco_usr_abc123...``).
        endpoint (str, optional): Ingestion URL. Defaults to ``https://ecotracelibrary.com/api/metrics/ingest``.
        timeout (float, optional): HTTP POST timeout in seconds. Defaults to 3.0.
    """

    DEFAULT_ENDPOINT = os.environ.get("ECOTRACE_INGEST_URL", "https://ecotracelibrary.com/api/metrics/ingest")

    def __init__(
        self,
        api_key: str,
        endpoint: Optional[str] = None,
        timeout: float = 3.0
    ) -> None:
        if not api_key or not isinstance(api_key, str):
            raise ValueError("CloudExporter requires a valid ingestion_key string.")

        self.api_key = api_key.strip()
        self.endpoint = (endpoint or self.DEFAULT_ENDPOINT).strip()
        self.timeout = timeout
        self.session = requests.Session()
        try:
            from .. import __version__ as _pkg_ver
        except ImportError:
            _pkg_ver = "1.5.1"

        self.session.headers.update({
            "Content-Type": "application/json",
            "X-EcoTrace-Key": self.api_key,
            "User-Agent": f"EcoTrace-Python-Client/{_pkg_ver}"
        })

    def export(
        self,
        carbon_emitted: float,
        func_name: str,
        duration: float,
        region: Optional[str] = None,
        run_id: Optional[str] = None,
        run_label: Optional[str] = None,
        **kwargs
    ) -> None:
        """Dispatches carbon metric payload to the EcoTrace Hosted Ingestion API.

        Args:
            carbon_emitted (float): Carbon emitted in gCO2.
            func_name (str): Tracked function name.
            duration (float): Execution duration in seconds.
            region (str, optional): ISO region code.
            run_id (str, optional): Unique session run identifier.
            run_label (str, optional): Optional human-readable run label.
        """
        payload = {
            "function": func_name or "unknown",
            "carbon_gco2": carbon_emitted,
            "duration_s": duration,
            "region": region or "GLOBAL",
            "run_id": run_id or "",
            "run_label": run_label or "",
            "recorded_at": time.time()
        }

        try:
            resp = self.session.post(self.endpoint, json=payload, timeout=self.timeout)
            if resp.status_code not in (200, 202):
                logger.debug(f"CloudExporter ingestion status: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.debug(f"CloudExporter connection error: {e}")
