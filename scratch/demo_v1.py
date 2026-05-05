"""EcoTrace v1.0 Feature Demo — Idle Baseline, Budget Enforcement, Session Summary."""
import time
from ecotrace import EcoTrace

# --- Custom callback: fires when budget is exceeded -----------------------
def budget_alert(total, limit):
    print(f"\n  [CALLBACK] Budget exceeded! {total:.6f} / {limit:.6f} gCO2\n")

# --- Initialize with carbon budget + callback ---
eco = EcoTrace(
    region_code="TR",
    carbon_limit=0.001,           # Very low budget to trigger alerts quickly
    on_budget_exceeded=budget_alert,
    session_summary=True           # atexit summary enabled
)

@eco.track
def light_work():
    """Simulates a quick computation."""
    return sum(i * i for i in range(50000))

@eco.track
def heavy_work():
    """Simulates a heavier computation."""
    return sum(i ** 0.5 for i in range(500000))

# --- Run tracked functions ---
print("\n--- Running light_work ---")
light_work()

print("\n--- Running heavy_work ---")
heavy_work()

# --- Check remaining budget programmatically ---
print(f"\nRemaining budget: {eco.remaining_budget}")
print(f"Equivalence: {eco.equivalence(eco.total_carbon)}")

# Session summary prints automatically at exit via atexit hook
