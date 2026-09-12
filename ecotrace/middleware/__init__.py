from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .django import EcoTraceDjangoMiddleware
    from .fastapi import EcoTraceMiddleware
    from .flask import EcoTraceFlask


def __getattr__(name: str):
    if name == "EcoTraceMiddleware":
        from .fastapi import EcoTraceMiddleware
        return EcoTraceMiddleware
    if name == "EcoTraceFlask":
        from .flask import EcoTraceFlask
        return EcoTraceFlask
    if name == "EcoTraceDjangoMiddleware":
        from .django import EcoTraceDjangoMiddleware
        return EcoTraceDjangoMiddleware
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["EcoTraceMiddleware", "EcoTraceFlask", "EcoTraceDjangoMiddleware"]
