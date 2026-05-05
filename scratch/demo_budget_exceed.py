"""EcoTrace v1.0 — Budget Exceeded Test."""
import time
from ecotrace import EcoTrace

def budget_alert(total, limit):
    print(f"  >>> CALLBACK FIRED: {total:.8f} gCO2 exceeded {limit:.8f} gCO2 <<<")

eco = EcoTrace(
    region_code="TR",
    carbon_limit=0.000001,  # Extremely low to guarantee exceed
    on_budget_exceeded=budget_alert,
    session_summary=True
)

@eco.track
def cpu_burner():
    return sum(i ** 0.5 for i in range(200000))

cpu_burner()
