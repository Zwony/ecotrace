"""EcoTrace — Centralized Logging Configuration.

Provides a pre-configured ``logging.Logger`` instance used across all
EcoTrace modules. Routes diagnostic messages through Python's standard
``logging`` framework so that integrators can attach their own handlers,
adjust verbosity, or silence EcoTrace output entirely.

Default behaviour:
    - Level: ``WARNING`` (production-safe; only warnings and errors appear)
    - Handler: ``StreamHandler`` to ``stderr``
    - Format: ``[EcoTrace] %(levelname)s: %(message)s``

Usage::

    from ecotrace.logger import logger
    logger.info("Measurement started")
    logger.warning("GPU driver unavailable, falling back")
"""

import logging

# Create the package-level logger
logger = logging.getLogger("ecotrace")

# Only add a handler if none exist (prevents duplicate handlers on reimport)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[EcoTrace] %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
