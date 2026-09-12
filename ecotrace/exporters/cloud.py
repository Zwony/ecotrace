import os
import time
import threading
from typing import Optional
import requests
from ..logger import logger
from ._retry_queue import RetryQueue


class CloudExporter:
    """Telemetry exporter for streaming carbon metrics directly to the EcoTrace Hosted Dashboard.

    Sends telemetry payloads matching the FastAPI ``MeasurementIn`` schema to the EcoTrace
    ingestion endpoint using the user's private ``ingestion_key`` (``eco_usr_...``).
    Failed transmissions are buffered to a lightweight disk queue and retried in the
    background with exponential backoff.

    Args:
        api_key (str): User's private ingestion key (e.g. ``eco_usr_abc123...``).
        endpoint (str, optional): Ingestion URL. Defaults to ``https://ecotracelibrary.com/api/metrics/ingest``.
        timeout (float, optional): HTTP POST timeout in seconds. Defaults to 3.0.
        retry_dir (str, optional): Directory for persisting pending retries. Defaults to ``~/.ecotrace/retry_queue``.
        max_queue_size (int, optional): Maximum number of buffered retry payloads. Defaults to 50.
    """

    DEFAULT_ENDPOINT = os.environ.get("ECOTRACE_INGEST_URL", "https://ecotracelibrary.com/api/metrics/ingest")

    def __init__(
        self,
        api_key: str,
        endpoint: Optional[str] = None,
        timeout: float = 3.0,
        retry_dir: Optional[str] = None,
        max_queue_size: int = 50
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
            _pkg_ver = "1.6.0"

        self.session.headers.update({
            "Content-Type": "application/json",
            "X-EcoTrace-Key": self.api_key,
            "User-Agent": f"EcoTrace-Python-Client/{_pkg_ver}"
        })

        self.queue = RetryQueue(retry_dir=retry_dir, max_size=max_queue_size)
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._worker_lock = threading.Lock()

        # If there are already items on disk from a previous run, start the worker
        if len(self.queue) > 0:
            self._ensure_worker()

    def _ensure_worker(self) -> None:
        """Spawns the background retry daemon thread if not already running."""
        with self._worker_lock:
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(
                    target=self._worker_loop,
                    name="EcoTrace-CloudRetryWorker",
                    daemon=True
                )
                self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Background loop draining pending disk payloads with exponential backoff."""
        backoff = 5.0
        while not self._stop_event.is_set():
            item = self.queue.peek_oldest()
            if item is None:
                backoff = 5.0
                self._wake_event.clear()
                self._wake_event.wait(timeout=30.0)
                continue

            file_path, payload = item
            success = False
            try:
                resp = self.session.post(self.endpoint, json=payload, timeout=self.timeout)
                if resp.status_code in (200, 202):
                    self.queue.delete(file_path)
                    success = True
                    backoff = 5.0
                else:
                    logger.debug(f"CloudExporter retry status: {resp.status_code}")
            except Exception as e:
                logger.debug(f"CloudExporter retry failed: {e}")

            if not success:
                self._wake_event.wait(timeout=backoff)
                backoff = min(60.0, backoff * 2.0)

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

        If the remote endpoint is unreachable, buffers the payload to disk and
        schedules background retry.

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

        # If backlog exists, route directly to queue to avoid blocking caller on failing endpoint
        if len(self.queue) > 0:
            self.queue.push(payload)
            self._ensure_worker()
            self._wake_event.set()
            return

        try:
            resp = self.session.post(self.endpoint, json=payload, timeout=self.timeout)
            if resp.status_code in (200, 202):
                return
            logger.debug(f"CloudExporter ingestion status: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.debug(f"CloudExporter connection error: {e}")

        # Buffer to disk upon initial failure
        self.queue.push(payload)
        self._ensure_worker()
        self._wake_event.set()

    def flush(self, timeout: float = 10.0) -> bool:
        """Synchronously attempts to drain all pending items in the retry queue.

        Args:
            timeout (float): Maximum seconds to spend draining the queue. Defaults to 10.0.

        Returns:
            bool: True if queue is empty, False if items remain.
        """
        end_time = time.time() + max(0.1, float(timeout))
        while time.time() < end_time and len(self.queue) > 0:
            item = self.queue.peek_oldest()
            if not item:
                break
            file_path, payload = item
            try:
                resp = self.session.post(self.endpoint, json=payload, timeout=self.timeout)
                if resp.status_code in (200, 202):
                    self.queue.delete(file_path)
                else:
                    break
            except Exception:
                break
        return len(self.queue) == 0

    def close(self) -> None:
        """Terminates background worker thread and releases session resources."""
        self._stop_event.set()
        self._wake_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        self.session.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
