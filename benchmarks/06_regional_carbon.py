"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 06: Cross-Region Variability
================================================================================
Demonstrates how identical compute workloads produce dramatically different
carbon footprints depending on the electrical grid's carbon intensity.
================================================================================
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from ecotrace import EcoTrace
from ecotrace.config import load_constants
from benchmarks.framework import EnvironmentSnapshot, BenchmarkStatistics

# --- Configuration -----------------------------------------------------------
WORKLOAD_DURATION_S = 10  # Fixed-duration CPU-intensive workload
MATRIX_SIZE = 1500        # NxN matrix for multiplication
MEASURED_RUNS = 5
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Regions sorted by carbon intensity (ascending) for dramatic contrast
REGIONS = [
    {"code": "SE", "name": "Sweden",        "notes": "Hydro + Nuclear dominant"},
    {"code": "NO", "name": "Norway",         "notes": "Hydro dominant (99%)"},
    {"code": "CH", "name": "Switzerland",    "notes": "Hydro + Nuclear"},
    {"code": "FR", "name": "France",         "notes": "Nuclear dominant (70%)"},
    {"code": "BR", "name": "Brazil",         "notes": "Hydro dominant"},
    {"code": "CA", "name": "Canada",         "notes": "Hydro + diverse mix"},
    {"code": "GB", "name": "United Kingdom", "notes": "Offshore wind growth"},
    {"code": "DE", "name": "Germany",        "notes": "Coal phase-out in progress"},
    {"code": "US", "name": "United States",  "notes": "Mixed grid (varies by state)"},
    {"code": "TR", "name": "Turkiye",        "notes": "Coal + gas + renewable mix"},
    {"code": "JP", "name": "Japan",          "notes": "LNG dominant post-Fukushima"},
    {"code": "CN", "name": "China",          "notes": "Coal dominant (60%)"},
    {"code": "IN", "name": "India",          "notes": "Coal dominant (70%)"},
    {"code": "ID", "name": "Indonesia",      "notes": "Coal dominant"},
    {"code": "ZA", "name": "South Africa",   "notes": "Coal dominant (85%)"},
]


def cpu_intensive_workload(duration_s: float = WORKLOAD_DURATION_S):
    """Executes a fixed-duration CPU-bound workload (matrix operations).

    The workload is designed to maintain consistent CPU utilization
    regardless of hardware speed, by running until a time limit is reached.

    Returns:
        dict: Metrics including total FLOPS and iterations completed.
    """
    iterations = 0
    t_start = time.perf_counter()

    while time.perf_counter() - t_start < duration_s:
        # Dense matrix multiplication -- CPU-heavy, predictable
        a = np.random.randn(MATRIX_SIZE, MATRIX_SIZE).astype(np.float32)
        b = np.random.randn(MATRIX_SIZE, MATRIX_SIZE).astype(np.float32)
        _ = a @ b
        iterations += 1

    actual_duration = time.perf_counter() - t_start
    # Approximate FLOPS: matrix multiply is ~2*N^3 FLOPS per iteration
    total_flops = iterations * 2 * (MATRIX_SIZE ** 3)

    return {
        "iterations": iterations,
        "actual_duration_s": actual_duration,
        "total_gflops": total_flops / 1e9,
    }


def main():
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: Cross-Region Carbon Variability")
    print("=" * 70)
    print(f" Workload: {WORKLOAD_DURATION_S}s CPU-bound (matrix {MATRIX_SIZE}x{MATRIX_SIZE})")
    print(f" Regions: {len(REGIONS)} countries | {MEASURED_RUNS} runs each")

    env = EnvironmentSnapshot()

    # Load carbon intensity map for reference
    base_dir = os.path.dirname(os.path.abspath(__file__))
    constants_path = os.path.join(base_dir, "..", "ecotrace", "constants.json")
    constants = load_constants(constants_path)
    intensity_map = constants.get("CARBON_INTENSITY_MAP", {})

    all_results = {}
    region_summaries = []

    for region in REGIONS:
        code = region["code"]
        name = region["name"]
        intensity = intensity_map.get(code, 475)

        print(f"\n{'-' * 70}")
        print(f"  {name} ({code}) -- {intensity} gCO2/kWh -- {region['notes']}")
        print(f"{'-' * 70}")

        # Create a fresh EcoTrace instance for each region
        eco = EcoTrace(
            region_code=code,
            check_updates=False,
            run_label=f"Region-{code}",
            quiet=True,
            session_summary=False,
        )

        stats = BenchmarkStatistics(f"{code}_{name}")

        for i in range(MEASURED_RUNS):
            carbon_before = eco.total_carbon
            energy_before = eco.total_energy_kwh

            with eco.track_block(f"workload_{code}_run_{i}"):
                t0 = time.perf_counter()
                workload_metrics = cpu_intensive_workload()
                duration = time.perf_counter() - t0

            carbon_delta = eco.total_carbon - carbon_before
            energy_delta = eco.total_energy_kwh - energy_before

            stats.add_run(
                duration=duration,
                carbon_gco2=carbon_delta,
                energy_wh=energy_delta * 1000,  # kWh -> Wh
                gflops=workload_metrics["total_gflops"],
            )

            sys.stdout.write(f"\r    Run {i+1}/{MEASURED_RUNS} -- {duration:.2f}s | "
                             f"Energy: {energy_delta*1000:.6f} Wh | "
                             f"Carbon: {carbon_delta:.8f} gCO2")
            sys.stdout.flush()

        print()

        summary = stats.summarize()
        region_summaries.append({
            "code": code,
            "name": name,
            "intensity_gco2_kwh": intensity,
            "notes": region["notes"],
            "energy_wh_mean": summary["energy_wh"]["mean"],
            "carbon_gco2_mean": summary["carbon_gco2"]["mean"],
            "duration_s_mean": summary["duration_s"]["mean"],
        })
        all_results[code] = stats

    # --- Summary Table (sorted by carbon intensity) ---
    print(f"\n{'=' * 70}")
    print(f"  CROSS-REGION CARBON VARIABILITY -- IDENTICAL WORKLOAD")
    print(f"{'=' * 70}")

    region_summaries.sort(key=lambda r: r["intensity_gco2_kwh"])
    lowest = region_summaries[0]
    highest = region_summaries[-1]

    print(f"\n  {'Region':<20} {'gCO2/kWh':>10} {'Energy (Wh)':>14} {'Carbon (gCO2)':>16} {'vs Lowest':>12}")
    print(f"  {'-' * 75}")

    for r in region_summaries:
        ratio = r["carbon_gco2_mean"] / lowest["carbon_gco2_mean"] if lowest["carbon_gco2_mean"] > 0 else 0
        print(f"  {r['name']:<20} {r['intensity_gco2_kwh']:>10} "
              f"{r['energy_wh_mean']:>14.6f} {r['carbon_gco2_mean']:>16.8f} {ratio:>11.1f}x")

    # Key insight
    if lowest["carbon_gco2_mean"] > 0:
        max_ratio = highest["carbon_gco2_mean"] / lowest["carbon_gco2_mean"]
        reduction = (1 - lowest["carbon_gco2_mean"] / highest["carbon_gco2_mean"]) * 100

        print(f"\n  +-----------------------------------------------------------------+")
        print(f"  |  KEY INSIGHT                                                    |")
        print(f"  |  The same workload in {highest['name']:<14} ({highest['code']}) produces {max_ratio:.0f}x MORE    |")
        print(f"  |  carbon than in {lowest['name']:<14} ({lowest['code']}).                      |")
        print(f"  |  Region selection alone can reduce emissions by {reduction:.0f}%.         |")
        print(f"  +-----------------------------------------------------------------+")

    # Save
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "environment": env.to_dict(),
        "config": {"workload_duration_s": WORKLOAD_DURATION_S, "matrix_size": MATRIX_SIZE,
                   "measured_runs": MEASURED_RUNS, "regions_tested": len(REGIONS)},
        "region_summaries": region_summaries,
        "statistics": {code: all_results[code].summarize() for code in all_results},
    }
    output_path = os.path.join(RESULTS_DIR, "06_regional_carbon.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
