"""
Minimal Celery task example with EcoTrace.

Requires: celery
"""

from celery import Celery

from ecotrace.core import EcoTrace
from ecotrace.plugins.celery import EcoTraceCelery


app = Celery(
    "ecotrace_example",
    broker="memory://",
    backend="cache+memory://",
)

app.conf.task_always_eager = True
app.conf.task_store_eager_result = True

eco = EcoTrace(quiet=True, check_updates=False)
EcoTraceCelery(ecotrace_instance=eco, log_to_csv=True)


@app.task
def workload() -> int:
    """Run a small workload as a Celery task."""
    total = 0
    for i in range(1_000_000):
        total += (i % 7) * (i % 13)
    return total


def main() -> None:
    """Run the task and report its measured emissions."""
    result = workload.delay()

    print(f"Task result: {result.get()}")
    print(f"Emissions: {eco.total_carbon:.8f} g CO2")


if __name__ == "__main__":
    main()
