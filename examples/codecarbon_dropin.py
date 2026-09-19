"""
Minimal example for migrating from CodeCarbon to EcoTrace.

The tracking API is intentionally kept compatible with the common
CodeCarbon EmissionsTracker workflow.
"""

from ecotrace import EmissionsTracker


def workload() -> int:
    """Run a small workload while emissions are being measured."""
    total = 0
    for i in range(1_000_000):
        total += (i % 7) * (i % 13)
    return total


def main() -> None:
    """Measure a workload with EcoTrace."""
    tracker = EmissionsTracker(
        project_name="codecarbon-migration-example",
        save_to_file=False,
    )

    tracker.start()
    workload()
    emissions_kg = tracker.stop()

    print(f"Emissions: {emissions_kg:.8f} kg CO2")
    print(f"Duration: {tracker.duration_seconds:.4f} seconds")


if __name__ == "__main__":
    main()