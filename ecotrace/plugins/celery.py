import time
import logging
from typing import Optional

from ecotrace.core import EcoTrace

try:
    from celery.signals import task_prerun, task_postrun, task_retry, task_revoked
except ImportError:
    task_prerun = None
    task_postrun = None
    task_retry = None
    task_revoked = None

logger = logging.getLogger("ecotrace.plugins.celery")

class EcoTraceCelery:
    """Celery plugin for tracking carbon emissions per background task.
    
    Attaches to Celery worker signals (prerun, postrun, retry) to accurately
    measure the footprint of individual jobs, including retries.
    
    Args:
        ecotrace_instance: Optional initialized EcoTrace instance.
        log_to_csv: Whether to log each task execution to ecotrace_log.csv.
    """
    
    def __init__(self, ecotrace_instance: Optional[EcoTrace] = None, log_to_csv: bool = False):
        if task_prerun is None:
            msg = "EcoTraceCelery requires 'celery'. Run: pip install ecotrace[celery]"
            logger.error(msg)
            return
            
        self.ecotrace = ecotrace_instance or EcoTrace(quiet=True, check_updates=False)
        self.log_to_csv = log_to_csv
        
        # State tracking per task_id to handle concurrency in thread/gevent pools
        self._task_state = {}
        
        # Connect signals
        task_prerun.connect(self._on_task_prerun, weak=False)
        task_postrun.connect(self._on_task_postrun, weak=False)
        task_retry.connect(self._on_task_retry, weak=False)
        task_revoked.connect(self._on_task_revoked, weak=False)
        
        logger.info("EcoTrace attached to Celery signals.")

    def _on_task_prerun(self, task_id, task, *args, **kwargs):
        """Triggered just before a task starts executing."""
        self._task_state[task_id] = time.perf_counter()
        self.ecotrace._start_cpu_monitor()

    def _on_task_postrun(self, task_id, task, *args, **kwargs):
        """Triggered when a task finishes (success or failure)."""
        self._finalize_task(task_id, task.name)

    def _on_task_retry(self, request, reason, einfo, **kwargs):
        """Triggered when a task throws a Retry exception.
        
        Celery raises a Retry exception which may bypass postrun depending on
        configuration, so we hook here to ensure the current attempt's emissions
        are logged independently.
        """
        self._finalize_task(request.id, request.task)

    def _on_task_revoked(self, request, terminated, signum, expired, **kwargs):
        """Triggered when a task is revoked or killed to prevent memory leaks."""
        self._task_state.pop(request.id, None)
        self.ecotrace._stop_cpu_monitor()

    def _finalize_task(self, task_id, task_name):
        """Resolves carbon metrics for a specific task attempt."""
        start_time = self._task_state.pop(task_id, None)
        if start_time is None:
            # Already finalized (e.g. by retry hook) or not tracked
            return
            
        self.ecotrace._stop_cpu_monitor()
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        try:
            avg_cpu = self.ecotrace._get_avg_cpu_in_range(start_time, end_time)
            carbon_emitted = self.ecotrace._compute_carbon(
                self.ecotrace.cpu_info['tdp'], avg_cpu, duration
            )
            
            if self.log_to_csv:
                func_name = f"Celery: {task_name}"
                self.ecotrace._accumulate_carbon(carbon_emitted, func_name, duration, avg_cpu)
                
        except Exception as e:
            logger.debug(f"EcoTrace Celery measurement failed: {e}")

# /* --- Hybrid End of File / Dosya Sonu --- */ #
# // EcoTrace Celery Plugin Integration // #
