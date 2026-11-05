"""Prometheus Pushgateway exporter for EcoTrace carbon metrics."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger("ecotrace.exporters.prometheus")

try:
    import requests  # type: ignore
except ImportError:
    requests = None

if TYPE_CHECKING:
    from ecotrace.core import EcoTrace

CONTENT_TYPE = "text/plain; version=0.0.4"
CARBON_METRIC = "ecotrace_carbon_emitted_gco2"
DURATION_METRIC = "ecotrace_execution_duration_seconds"


def _escape_label_value(value: str) -> str:
    """Escapes a label value as the Prometheus text format requires."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def format_metrics(
    carbon_emitted: float, func_name: str, duration: float, run_id: str
) -> str:
    """Formats one measurement in the Prometheus text exposition format.

    Returns two gauges, each labelled with ``function`` and ``run_id``,
    ending with the newline the Pushgateway requires.
    """
    labels = '{function="%s",run_id="%s"}' % (
        _escape_label_value(func_name),
        _escape_label_value(run_id),
    )
    lines = [
        "# HELP %s Carbon emitted by the measured function, in gCO2."
        % CARBON_METRIC,
        "# TYPE %s gauge" % CARBON_METRIC,
        "%s%s %r" % (CARBON_METRIC, labels, float(carbon_emitted)),
        "# HELP %s Execution time of the measured function, in seconds."
        % DURATION_METRIC,
        "# TYPE %s gauge" % DURATION_METRIC,
        "%s%s %r" % (DURATION_METRIC, labels, float(duration)),
    ]
    return "\n".join(lines) + "\n"


class PrometheusExporter:
    """Pushes EcoTrace metrics to a Prometheus Pushgateway.

    After each measurement it POSTs two gauges,
    ``ecotrace_carbon_emitted_gco2`` and
    ``ecotrace_execution_duration_seconds``, labelled with the function
    name and run ID, to ``<url>/metrics/job/<job>``. POST adds to the
    job's group, so samples from different functions and runs coexist.
    Network and HTTP errors are logged and never raised.

    Example::

        from ecotrace import EcoTrace
        from ecotrace.exporters import PrometheusExporter

        eco = EcoTrace()
        PrometheusExporter(eco, url="http://localhost:9091")

        @eco.track
        def train():
            ...

    Args:
        ecotrace_instance: The initialized EcoTrace core instance to
            attach to.
        url: Base URL of the Pushgateway, e.g. ``http://localhost:9091``.
        job: Pushgateway job name (default ``"ecotrace"``).
        headers: Optional dict of extra HTTP headers (e.g. for auth).
        timeout: Request timeout in seconds (default 5).
    """

    def __init__(
        self,
        ecotrace_instance: EcoTrace,
        url: str,
        job: str = "ecotrace",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5,
    ):
        if requests is None:
            logger.error(
                "PrometheusExporter requires 'requests'. "
                "Please install requests."
            )
            self.url = None
            return

        self.ecotrace = ecotrace_instance
        self.url = url
        self.job = job
        self.headers = headers or {}
        self.timeout = timeout
        self.push_url = "%s/metrics/job/%s" % (
            url.rstrip("/"),
            quote(job, safe=""),
        )

        self.ecotrace.add_exporter(self)
        logger.info(
            "Prometheus Exporter attached to EcoTrace (push url: %s).",
            self.push_url,
        )

    def export(
        self,
        carbon_emitted: float,
        func_name: str,
        duration: float,
        region: str,
        run_id: Optional[str] = None,
        run_label: Optional[str] = None,
        **kwargs,
    ):
        """Called by EcoTrace whenever a measurement completes.

        Args:
            carbon_emitted: The measured footprint in gCO2.
            func_name: The name of the function or block that was tracked.
            duration: The execution time in seconds.
            region: The grid intensity region code used (not exported).
            run_id: The EcoTrace run ID; defaults to the instance's.
            run_label: Unused; accepted for the exporter interface.
        """
        if not self.url or requests is None:
            return

        if run_id is None:
            run_id = getattr(self.ecotrace, "_run_id", "")
        body = format_metrics(carbon_emitted, func_name, duration, run_id)

        try:
            req_headers = {"Content-Type": CONTENT_TYPE}
            req_headers.update(self.headers)
            response = requests.post(
                self.push_url,
                data=body.encode("utf-8"),
                headers=req_headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as e:
            logger.debug("Failed to push metrics to Pushgateway: %s", e)
