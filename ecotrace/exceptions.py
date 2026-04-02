"""EcoTrace - Custom Exceptions

This module defines domain-specific exceptions for EcoTrace to provide
meaningful, programmatic error handling instead of generic built-in failures.
"""

class EcoTraceError(Exception):
    """Base exception for all EcoTrace-related errors."""
    pass

class EcoTraceConfigurationError(EcoTraceError):
    """Raised when EcoTrace is initialized with invalid parameters (e.g. negative GPU index)."""
    pass

class LiveGridAPIError(EcoTraceError):
    """Raised when the real-time grid intensity API fails or times out."""
    pass

class GPUMonitoringError(EcoTraceError):
    """Raised when the GPU monitoring thread encounters an unrecoverable failure."""
    pass

class CPUMonitoringError(EcoTraceError):
    """Raised when the CPU/process tree cannot be read due to permission or lifecycle issues."""
    pass

class AIInsightsError(EcoTraceError):
    """Raised when Google Gemini fails to generate insights."""
    pass

class ReportGenerationError(EcoTraceError):
    """Raised when the PDF report cannot be compiled or saved to disk."""
    pass

class EcoTraceUpdateError(EcoTraceError):
    """Raised (or logged) when the auto-updater fails to connect to PyPI."""
    pass
