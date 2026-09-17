__version__ = "1.6.1"

from .core import EcoTrace
from .ml import EcoTraceML, ecotrace_ml
from .tracker import EmissionsTracker, OfflineEmissionsTracker, track_emissions

__all__ = [
    "EcoTrace",
    "EcoTraceML",
    "ecotrace_ml",
    "EmissionsTracker",
    "OfflineEmissionsTracker",
    "track_emissions",
    "__version__",
]
