__version__ = "1.6.0"

from .core import EcoTrace
from .ml import EcoTraceML, ecotrace_ml

__all__ = ["EcoTrace", "EcoTraceML", "ecotrace_ml", "__version__"]