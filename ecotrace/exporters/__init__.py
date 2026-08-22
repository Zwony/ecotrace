"""
EcoTrace Exporters Package

Provides integrations for pushing carbon metrics to external
observability platforms and telemetry aggregators.
"""

def __getattr__(name: str):
    if name == "CloudExporter":
        from .cloud import CloudExporter
        return CloudExporter
    if name == "OTelExporter":
        from .otel import OTelExporter
        return OTelExporter
    if name == "WebhookExporter":
        from .webhook import WebhookExporter
        return WebhookExporter
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["CloudExporter", "OTelExporter", "WebhookExporter"]
