"""
EcoTrace Exporters Package

Provides integrations for pushing carbon metrics to external
observability platforms and telemetry aggregators (``CloudExporter``,
``OTelExporter``, ``WebhookExporter``), plus local summary exporters
(``to_markdown``, ``to_html``) that render the session dictionary from
``EcoTrace.get_summary()`` as Markdown or HTML reports.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cloud import CloudExporter
    from .otel import OTelExporter
    from .summary import to_html, to_markdown
    from .prometheus import PrometheusExporter
    from .webhook import WebhookExporter


def __getattr__(name: str):
    if name == "CloudExporter":
        from .cloud import CloudExporter
        return CloudExporter
    if name == "OTelExporter":
        from .otel import OTelExporter
        return OTelExporter
    if name == "PrometheusExporter":
        from .prometheus import PrometheusExporter
        return PrometheusExporter
    if name == "WebhookExporter":
        from .webhook import WebhookExporter
        return WebhookExporter
    if name == "to_markdown":
        from .summary import to_markdown
        return to_markdown
    if name == "to_html":
        from .summary import to_html
        return to_html
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "CloudExporter",
    "OTelExporter",
    "WebhookExporter",
    "to_html",
    "to_markdown",
    "PrometheusExporter",
]
