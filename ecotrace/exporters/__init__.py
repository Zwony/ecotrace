"""
EcoTrace Exporters Package

Provides integrations for pushing carbon metrics to external
observability platforms and telemetry aggregators.
"""

from .otel import OTelExporter

__all__ = ["OTelExporter"]
