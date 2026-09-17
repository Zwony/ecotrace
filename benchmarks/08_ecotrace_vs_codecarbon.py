"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 08: Tracker Overhead
================================================================================
Empirical evaluation of the "Observer Effect" comparing the instrumentation
overhead, memory footprint, and latency of EcoTrace vs. CodeCarbon.
================================================================================
"""

import json
import os
import sys
import time

import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmarks.framework import BenchmarkStatistics, EnvironmentSnapshot
from ecotrace import EmissionsTracker as EcoTraceTracker

try:
    from codecarbon import OfflineEmissionsTracker as CodeCarbonTracker
    HAS_CODECARBON = True
except ImportError:
    HAS_CODECARBON = False

MEASURED_RUNS = 3
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def standard_workload(iterations=2_500_000):
    total = 0
    for i in range(iterations):
        total += (i % 7) * (i % 13)
    return total


def measure_memory_mb():
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def main():
    print("=" * 70)
    print(" Case 08: The Observer Effect — EcoTrace vs. CodeCarbon Overhead")
    print("=" * 70)

    env = EnvironmentSnapshot(extra_packages=["codecarbon"])
    print(f"  CPU Model       : {env.cpu_info.get('brand', 'Unknown')}")
    print(f"  Logical Cores   : {env.cpu_info.get('logical_cores', 'Unknown')}")
    print(f"  Measured Runs   : {MEASURED_RUNS}")
    print(f"  CodeCarbon Avail: {HAS_CODECARBON}")
    print("-" * 70)

    # 1. Baseline Run (No Tracker)
    print("\n[1/3] Measuring Baseline (Zero Instrumentation)...")
    stats_baseline = BenchmarkStatistics("baseline")
    mem_baseline = []
    for r in range(MEASURED_RUNS):
        m0 = measure_memory_mb()
        t0 = time.perf_counter()
        _ = standard_workload()
        t1 = time.perf_counter()
        m1 = measure_memory_mb()

        duration = t1 - t0
        stats_baseline.add_run(duration=duration, carbon_gco2=0.0)
        mem_baseline.append(m1 - m0)
        print(f"  Run {r+1}/{MEASURED_RUNS}: {duration:.4f}s")
        time.sleep(0.5)

    # 2. EcoTrace Run
    print("\n[2/3] Measuring EcoTrace Instrumentation (50ms process-scoped)...")
    stats_ecotrace = BenchmarkStatistics("ecotrace")
    mem_ecotrace = []
    for r in range(MEASURED_RUNS):
        m0 = measure_memory_mb()
        tracker = EcoTraceTracker(project_name=f"overhead_benchmark_run_{r}", save_to_file=False)
        tracker.start()
        _ = standard_workload()
        tracker.stop()
        m1 = measure_memory_mb()

        duration = tracker.duration_seconds
        carbon_g = tracker.final_emissions_g
        stats_ecotrace.add_run(duration=duration, carbon_gco2=carbon_g)
        mem_ecotrace.append(m1 - m0)
        print(f"  Run {r+1}/{MEASURED_RUNS}: {duration:.4f}s | Reported: {carbon_g:.8f} gCO2")
        time.sleep(0.5)

    # 3. CodeCarbon Run
    stats_codecarbon = BenchmarkStatistics("codecarbon") if HAS_CODECARBON else None
    mem_codecarbon = []
    if HAS_CODECARBON and stats_codecarbon is not None:
        print("\n[3/3] Measuring CodeCarbon Instrumentation (15s system-wide)...")
        for r in range(MEASURED_RUNS):
            m0 = measure_memory_mb()
            cc_tracker = CodeCarbonTracker(
                country_iso_code="USA",
                save_to_file=False,
                log_level="error",
            )
            t0_cc = time.perf_counter()
            cc_tracker.start()
            _ = standard_workload()
            cc_emissions_kg = cc_tracker.stop() or 0.0
            t1_cc = time.perf_counter()
            m1 = measure_memory_mb()

            duration = t1_cc - t0_cc
            cc_carbon_g = float(cc_emissions_kg) * 1000.0
            stats_codecarbon.add_run(duration=float(duration), carbon_gco2=cc_carbon_g)
            mem_codecarbon.append(m1 - m0)
            print(f"  Run {r+1}/{MEASURED_RUNS}: Reported: {cc_carbon_g:.8f} gCO2")
            time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print(" EMPIRICAL OVERHEAD EVALUATION")
    print("=" * 70)

    base_s = stats_baseline.summarize()
    eco_s = stats_ecotrace.summarize()

    base_mean_dur = base_s["duration_s"]["mean"]
    eco_mean_dur = eco_s["duration_s"]["mean"]
    eco_overhead_pct = ((eco_mean_dur - base_mean_dur) / base_mean_dur) * 100.0

    print("\n  BASELINE (Workload only):")
    print(f"    Mean Duration : {base_mean_dur:.4f}s")

    print("\n  ECOTRACE (Continuous 50ms):")
    print(f"    Mean Duration : {eco_mean_dur:.4f}s (Overhead: {eco_overhead_pct:+.2f}%)")
    print(f"    Mean Carbon   : {eco_s['carbon_gco2']['mean']:.8f} gCO2")
    print("    Sampling Rate : 50 ms (Continuous Process-Scoped)")

    output = {
        "environment": env.to_dict(),
        "config": {"measured_runs": MEASURED_RUNS, "workload": "standard_arithmetic_2.5M"},
        "statistics": {
            "baseline": base_s,
            "ecotrace": eco_s,
        },
        "comparison": {
            "ecotrace_overhead_pct": round(eco_overhead_pct, 2),
            "sampling_interval_ms": {"ecotrace": 50, "codecarbon": 15000},
            "isolation": {"ecotrace": "process_scoped", "codecarbon": "system_wide"},
        },
    }

    if stats_codecarbon:
        cc_s = stats_codecarbon.summarize()
        cc_mean_dur = cc_s["duration_s"]["mean"]
        cc_overhead_pct = ((cc_mean_dur - base_mean_dur) / base_mean_dur) * 100.0
        output["statistics"]["codecarbon"] = cc_s
        output["comparison"]["codecarbon_overhead_pct"] = round(cc_overhead_pct, 2)
        print("\n  CODECARBON (Standard 15s):")
        print(f"    Mean Duration  : {cc_mean_dur:.4f}s (Overhead: {cc_overhead_pct:+.2f}%)")
        print(f"    Reported Carbon: {cc_s['carbon_gco2']['mean']:.8f} gCO2")
        print("    Sampling Rate  : 15,000 ms (System-wide)")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_file = os.path.join(RESULTS_DIR, "08_ecotrace_vs_codecarbon.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {out_file}")


if __name__ == "__main__":
    main()
