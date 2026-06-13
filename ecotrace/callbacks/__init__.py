"""EcoTrace ML framework callbacks (v1.3.0).

Provides per-epoch carbon tracking integrations for popular ML frameworks.
All framework imports are **lazy** — installing EcoTrace never requires
PyTorch or TensorFlow as a dependency.

Usage::

    # PyTorch (manual loop)
    from ecotrace.callbacks.pytorch import EcoTracePyTorchCallback

    # Keras / TensorFlow (model.fit)
    from ecotrace.callbacks.keras import EcoTraceKerasCallback
"""

# Nothing is imported at package level — framework imports are deferred to
# the individual module files so the base ecotrace install stays lightweight.
