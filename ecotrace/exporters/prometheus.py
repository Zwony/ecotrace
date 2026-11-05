"""Prometheus Pushgateway exporter for EcoTrace carbon metrics."""

from __future__ import annotations

import base64
import logging
import math
from typing import TYPE_CHECKING, Dict, Optional

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


def _format_value(value: float) -> str:
    """Formats a sample value, spelling NaN and infinity as Prometheus does."""
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "+Inf" if value > 0 else "-Inf"
    return repr(value)


def _format_metrics(
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
        "%s%s %s" % (CARBON_METRIC, labels, _format_value(carbon_emitted)),
        "# HELP %s Execution time of the measured function, in seconds."
        % DURATION_METRIC,
        "# TYPE %s gauge" % DURATION_METRIC,
        "%s%s %s" % (DURATION_METRIC, labels, _format_value(duration)),
    ]
    return "\n".join(lines) + "\n"


def _grouping_segment(name: str, value: str) -> str:
    """Builds one ``<name>@base64/<value>`` grouping key path segment.

    Base64 (URL-safe) lets any value through the URL path, including
    ``/``; the Pushgateway reads an empty value as ``=``.
    """
    encoded = base64.urlsafe_b64encode(str(value).encode("utf-8"))
    encoded = encoded.decode("ascii").rstrip("=")
    return "%s@base64/%s" % (name, encoded or "=")


class PrometheusExporter:
    """Pushes EcoTrace metrics to a Prometheus Pushgateway.

    After each measurement it POSTs two gauges,
    ``ecotrace_carbon_emitted_gco2`` and
    ``ecotrace_execution_duration_seconds``, labelled with the function
    name and run ID. The function name and run ID are also the push's
    grouping key, so each push goes to
    ``<url>/metrics/job/<job>/function@base64/.../run_id@base64/...``.
    The Pushgateway replaces metrics only within a group, so every
    function and run keeps its own latest values instead of overwriting
    each other. Network and HTTP errors are logged and never raised.

    The Pushgateway keeps groups until they are deleted, and each
    EcoTrace process has a new run ID, so groups accumulate over runs.
    Delete old ones with an HTTP DELETE on the same URL, or through the
    Pushgateway's API or web UI.

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
        self.job_url = "%s/metrics/%s" % (
            url.rstrip("/"),
            _grouping_segment("job", job),
        )

        self.ecotrace.add_exporter(self)
        logger.info(
            "Prometheus Exporter attached to EcoTrace (pushgateway: %s).",
            self.url,
        )

    def push_url(self, func_name: str, run_id: str) -> str:
        """Returns the Pushgateway URL for one function and run's group."""
        return "%s/%s/%s" % (
            self.job_url,
            _grouping_segment("function", func_name),
            _grouping_segment("run_id", run_id),
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
        body = _format_metrics(carbon_emitted, func_name, duration, run_id)

        try:
            req_headers = {"Content-Type": CONTENT_TYPE}
            req_headers.update(self.headers)
            response = requests.post(
                self.push_url(func_name, run_id),
                data=body.encode("utf-8"),
                headers=req_headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as e:
            logger.debug("Failed to push metrics to Pushgateway: %s", e)
