"""EcoTrace LangChain callback — per-call carbon and energy tracking for LLMs.

Measures the process-scoped energy and carbon footprint of every LLM or chat
model invocation made through LangChain, including calls made inside chains
and agents. LangChain is **not** a hard dependency: ``langchain_core`` is only
imported if it is installed, and this module is always safe to import.

Example::

    from ecotrace.callbacks import EcoTraceLangChainCallback

    cb = EcoTraceLangChainCallback(project_name="rag-pipeline")
    llm.invoke("Summarise this document...", config={"callbacks": [cb]})

    print(cb.total_emissions_g)   # gCO2 across all LLM calls
    print(cb.records)             # per-call breakdown

Each LLM call is keyed by LangChain's ``run_id``, so concurrent calls
(``batch()``, async agents, parallel tool use) are measured independently.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from ..logger import logger
from ..tracker import EmissionsTracker

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler
else:
    try:
        from langchain_core.callbacks import BaseCallbackHandler
    except ImportError:
        try:
            from langchain.callbacks.base import BaseCallbackHandler
        except ImportError:
            class BaseCallbackHandler:
                """Minimal stand-in used when LangChain is not installed."""

                raise_error: bool = False
                run_inline: bool = False


class EcoTraceLangChainCallback(BaseCallbackHandler):
    """LangChain callback handler for per-invocation carbon and energy tracking.

    Hooks into ``on_llm_start`` / ``on_chat_model_start`` and ``on_llm_end`` /
    ``on_llm_error`` to measure each model call separately. Results are kept
    in :attr:`records` and summed into :attr:`total_emissions_g` and
    :attr:`total_emissions_kg`.

    Args:
        project_name: Label written to logs and the CSV audit trail.
        country_iso_code: ISO country code used for carbon intensity.
        region: Alternative region code (used if ``country_iso_code`` is unset).
        output_dir: Directory for the optional CSV output file.
        output_file: CSV file name. If set, one row is appended per LLM call.
        verbose: If True, logs a one-line summary after each call.
        **kwargs: Extra keyword arguments forwarded to ``EmissionsTracker``.
    """

    def __init__(
        self,
        project_name: str = "LangChain LLM",
        country_iso_code: Optional[str] = None,
        region: Optional[str] = None,
        output_dir: Optional[str] = None,
        output_file: Optional[str] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.project_name = project_name
        self.verbose = verbose
        self._tracker_kwargs: Dict[str, Any] = dict(
            project_name=project_name,
            country_iso_code=country_iso_code,
            region=region,
            output_dir=output_dir,
            output_file=output_file,
            **kwargs,
        )

        self._lock = threading.Lock()
        self._active: Dict[UUID, Dict[str, Any]] = {}
        # Stopped trackers are reused so each call does not re-detect hardware.
        self._idle_trackers: List[EmissionsTracker] = []

        self.records: List[Dict[str, Any]] = []
        self.total_emissions_g: float = 0.0
        self.total_emissions_kg: float = 0.0
        self.total_duration_s: float = 0.0

    # ------------------------------------------------------------------ #
    # LangChain hooks
    # ------------------------------------------------------------------ #

    def on_llm_start(
        self,
        serialized: Optional[Dict[str, Any]],
        prompts: List[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Starts measurement for a completion-style LLM call."""
        self._begin(run_id, serialized, kwargs)

    def on_chat_model_start(
        self,
        serialized: Optional[Dict[str, Any]],
        messages: List[List[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Starts measurement for a chat model call."""
        self._begin(run_id, serialized, kwargs)

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Stops measurement and records emissions for a finished call."""
        self._finish(run_id, status="success", response=response)

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        """Stops measurement for a failed call so no tracker is left running."""
        self._finish(run_id, status="error", error=error)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _begin(self, run_id: UUID, serialized: Optional[Dict[str, Any]], kwargs: Dict[str, Any]) -> None:
        with self._lock:
            if run_id in self._active:
                return
            tracker = self._idle_trackers.pop() if self._idle_trackers else None

        if tracker is None:
            tracker = EmissionsTracker(**self._tracker_kwargs)
        tracker.start()

        with self._lock:
            self._active[run_id] = {
                "tracker": tracker,
                "model": _model_name(serialized, kwargs),
                "started_at": time.time(),
            }

    def _finish(
        self,
        run_id: UUID,
        status: str,
        response: Any = None,
        error: Optional[BaseException] = None,
    ) -> None:
        with self._lock:
            entry = self._active.pop(run_id, None)
        if entry is None:
            return

        tracker: EmissionsTracker = entry["tracker"]
        emissions_kg = tracker.stop()
        emissions_g = tracker.final_emissions_g
        duration_s = tracker.duration_seconds

        record: Dict[str, Any] = {
            "run_id": str(run_id),
            "model": entry["model"],
            "status": status,
            "started_at": entry["started_at"],
            "duration_s": duration_s,
            "emissions_g": emissions_g,
            "emissions_kg": emissions_kg,
        }
        token_usage = _token_usage(response)
        if token_usage:
            record["token_usage"] = token_usage
        if error is not None:
            record["error"] = repr(error)

        with self._lock:
            self.records.append(record)
            self.total_emissions_g += emissions_g
            self.total_emissions_kg += emissions_kg
            self.total_duration_s += duration_s
            self._idle_trackers.append(tracker)

        if self.verbose:
            logger.info(
                f"[EcoTrace] LLM call ({entry['model']}, {status}) took {duration_s:.2f}s "
                f"and emitted {emissions_g:.6f} gCO2."
            )

    @property
    def active_runs(self) -> int:
        """Number of LLM calls currently being measured."""
        with self._lock:
            return len(self._active)

    def summary(self) -> Dict[str, Any]:
        """Returns aggregate totals across all recorded LLM calls."""
        with self._lock:
            return {
                "project_name": self.project_name,
                "calls": len(self.records),
                "errors": sum(1 for r in self.records if r["status"] == "error"),
                "total_duration_s": self.total_duration_s,
                "total_emissions_g": self.total_emissions_g,
                "total_emissions_kg": self.total_emissions_kg,
            }

    def reset(self) -> None:
        """Clears recorded results. Calls still in flight are unaffected."""
        with self._lock:
            self.records.clear()
            self.total_emissions_g = 0.0
            self.total_emissions_kg = 0.0
            self.total_duration_s = 0.0


def _model_name(serialized: Optional[Dict[str, Any]], kwargs: Dict[str, Any]) -> str:
    """Best-effort model name from LangChain's callback payload."""
    params = kwargs.get("invocation_params") or {}
    for key in ("model", "model_name", "model_id"):
        if params.get(key):
            return str(params[key])
    metadata = kwargs.get("metadata") or {}
    if metadata.get("ls_model_name"):
        return str(metadata["ls_model_name"])
    if serialized:
        if serialized.get("name"):
            return str(serialized["name"])
        ids = serialized.get("id")
        if isinstance(ids, list) and ids:
            return str(ids[-1])
    return "unknown"


def _token_usage(response: Any) -> Optional[Dict[str, Any]]:
    """Extracts token usage from an ``LLMResult`` if the provider reported it."""
    llm_output = getattr(response, "llm_output", None)
    if isinstance(llm_output, dict):
        usage = llm_output.get("token_usage") or llm_output.get("usage")
        if isinstance(usage, dict) and usage:
            return dict(usage)
    return None


EcoTraceLangChainHandler = EcoTraceLangChainCallback
