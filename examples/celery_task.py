"""Instrumenting background Celery tasks with EcoTraceCelery.

Requires the optional Celery dependencies: pip install ecotrace[celery]
"""

from celery import Celery

from ecotrace.plugins.celery import EcoTraceCelery

app = Celery("tasks", broker="redis://localhost:6379/0")

eco = EcoTraceCelery(log_to_csv=True)


@app.task
def heavy_job(n: int) -> int:
    return sum(range(n))


if __name__ == "__main__":
    # emissions per task execution are recorded on task_postrun,
    # including retries handled by task_retry
    result = heavy_job.delay(1_000_000)
    print(f"task id {result.id} submitted, tracking active on worker signals")
