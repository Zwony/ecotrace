import logging
from typing import Optional

logger = logging.getLogger("ecotrace.exporters.otel")

try:
    from opentelemetry import metrics
    from opentelemetry.metrics import MeterProvider, Meter
except ImportError:
    metrics = None
    MeterProvider = None
    Meter = None

from ecotrace.core import EcoTrace

class OTelExporter:
    """OpenTelemetry metrics exporter for EcoTrace carbon emissions.
    
    Creates a counter metric 'ecotrace.carbon.emitted' to record grams of CO2
    emitted by the measured Python processes. This enables streaming carbon
    footprint data to Grafana, Datadog, Prometheus, etc.
    
    Args:
        ecotrace_instance: The initialized EcoTrace core instance to attach to.
        meter_provider: Optional OpenTelemetry MeterProvider. If None, uses the global provider.
        meter_name: Name of the OTel meter (default 'ecotrace.exporter.otel').
    """
    
    def __init__(
        self, 
        ecotrace_instance: EcoTrace, 
        meter_provider: Optional[MeterProvider] = None,
        meter_name: str = "ecotrace.exporter.otel"
    ):
        if metrics is None:
            msg = "OTelExporter requires 'opentelemetry-api'. Run: pip install ecotrace[otel]"
            logger.error(msg)
            # Fails gracefully during initialization if missing
            self._carbon_counter = None
            return
            
        self.ecotrace = ecotrace_instance
        self.meter_provider = meter_provider
        self.meter_name = meter_name
        
        # Get meter from provider or global
        if self.meter_provider:
            self.meter = self.meter_provider.get_meter(self.meter_name)
        else:
            self.meter = metrics.get_meter(self.meter_name)
            
        # Create synchronous counter for carbon mass (gCO2)
        self._carbon_counter = self.meter.create_counter(
            name="ecotrace.carbon.emitted",
            description="Total grams of CO2 emitted by the application",
            unit="g",
        )
        
        # Attach self to the EcoTrace engine
        self.ecotrace.add_exporter(self)
        logger.info(f"OpenTelemetry Exporter attached to EcoTrace (meter: {self.meter_name}).")

    def export(self, carbon_emitted: float, func_name: str, duration: float, region: str):
        """Called synchronously by EcoTrace whenever a measurement completes.
        
        Args:
            carbon_emitted: The measured footprint in gCO2.
            func_name: The name of the function or block that was tracked.
            duration: The execution time in seconds.
            region: The grid intensity region code used (e.g., 'US', 'DE').
        """
        if self._carbon_counter is None:
            return
            
        attributes = {
            "ecotrace.function": func_name,
            "ecotrace.region": region,
        }
        
        try:
            self._carbon_counter.add(carbon_emitted, attributes=attributes)
        except Exception as e:
            logger.debug(f"Failed to record OTel metric: {e}")

# /* --- Hybrid End of File / Dosya Sonu --- */ #
# // EcoTrace OpenTelemetry Exporter Integration // #
