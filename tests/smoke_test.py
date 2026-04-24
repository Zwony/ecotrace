# Smoke test for EcoTrace CLI validation
import time

def compute_task():
    """Simple CPU-bound task for CLI testing."""
    # Heavier workload to ensure CPU spike is visible (2M instead of 200k)
    total = sum(i * i for i in range(2_000_000))
    return total

if __name__ == "__main__":
    print("[smoke_test] Starting...")
    result = compute_task()
    print(f"[smoke_test] Result: {result}")
    print("[smoke_test] Done.")
