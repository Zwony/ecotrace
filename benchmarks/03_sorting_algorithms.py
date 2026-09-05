"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 03: Sorting Algorithms
================================================================================
Quantifies the carbon cost of algorithmic complexity by measuring energy
consumption across sorting algorithms at various input scales.
================================================================================
"""

import os
import sys
import time
import json
import random
import heapq

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from ecotrace import EcoTrace
from benchmarks.framework import EnvironmentSnapshot, BenchmarkStatistics

# --- Configuration -----------------------------------------------------------
SCALES = [50_000, 100_000, 500_000, 1_000_000]
MEASURED_RUNS = 3
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def generate_random_array(n: int, seed: int = 42) -> list:
    """Generates a reproducible random integer array."""
    rng = random.Random(seed)
    return [rng.randint(0, n * 10) for _ in range(n)]


# --- Sorting Algorithm Implementations ---------------------------------------

def python_builtin_sort(arr: list) -> list:
    """Python's built-in Timsort (C implementation)."""
    return sorted(arr)


def numpy_sort(arr: list) -> np.ndarray:
    """NumPy's introsort (C/Fortran implementation)."""
    a = np.array(arr)
    return np.sort(a)


def merge_sort(arr: list) -> list:
    """Pure Python merge sort -- O(n log n) guaranteed."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def heap_sort(arr: list) -> list:
    """Python heapq-based heap sort -- O(n log n)."""
    heapq.heapify(arr_copy := list(arr))
    return [heapq.heappop(arr_copy) for _ in range(len(arr_copy))]


def insertion_sort(arr: list) -> list:
    """Pure Python insertion sort -- O(n^2). Only used for small N."""
    result = list(arr)
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = key
    return result


# --- Algorithm Registry -------------------------------------------------------

ALGORITHMS = {
    "python_builtin": {"fn": python_builtin_sort, "max_n": None,      "complexity": "O(n log n)"},
    "numpy_sort":     {"fn": numpy_sort,          "max_n": None,      "complexity": "O(n log n)"},
    "merge_sort":     {"fn": merge_sort,          "max_n": 1_000_000, "complexity": "O(n log n)"},
    "heap_sort":      {"fn": heap_sort,           "max_n": 5_000_000, "complexity": "O(n log n)"},
    "insertion_sort":  {"fn": insertion_sort,       "max_n": 50_000,    "complexity": "O(n^2)"},
}


def main():
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: Sorting Algorithm Carbon Fingerprints")
    print("=" * 70)

    env = EnvironmentSnapshot()
    eco = EcoTrace(check_updates=False, run_label="Sorting-Benchmark")

    all_results = {}

    for scale in SCALES:
        print(f"\n{'=' * 70}")
        print(f"  SCALE: {scale:,} elements")
        print(f"{'=' * 70}")

        base_array = generate_random_array(scale)
        scale_results = {}

        for algo_name, algo_cfg in ALGORITHMS.items():
            max_n = algo_cfg["max_n"]
            if max_n is not None and scale > max_n:
                print(f"  [{algo_name}] Skipped (N={scale:,} exceeds max_n={max_n:,})")
                continue

            stats = BenchmarkStatistics(f"{algo_name}_{scale}")

            print(f"  [{algo_name}] {algo_cfg['complexity']} -- {MEASURED_RUNS} runs...")

            for i in range(MEASURED_RUNS):
                arr_copy = list(base_array)
                carbon_before = eco.total_carbon

                with eco.track_block(f"{algo_name}_{scale}_run_{i}"):
                    t0 = time.perf_counter()
                    result = algo_cfg["fn"](arr_copy)
                    duration = time.perf_counter() - t0

                carbon_delta = eco.total_carbon - carbon_before
                stats.add_run(duration=duration, carbon_gco2=carbon_delta)

                sys.stdout.write(f"\r    Run {i+1}/{MEASURED_RUNS} -- "
                                 f"{duration:.4f}s, {carbon_delta:.8f} gCO2")
                sys.stdout.flush()

            print()
            scale_results[algo_name] = stats

        all_results[str(scale)] = scale_results

    # --- Summary Table ---
    print(f"\n{'=' * 70}")
    print(f"  RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n  {'Algorithm':<20} {'N':>12} {'Duration (s)':>15} {'Carbon (gCO2)':>18} {'Complexity':<12}")
    print(f"  {'-' * 80}")

    for scale_str, scale_data in all_results.items():
        for algo_name, stats in scale_data.items():
            s = stats.summarize()
            complexity = ALGORITHMS[algo_name]["complexity"]
            print(f"  {algo_name:<20} {scale_str:>12} {s['duration_s']['mean']:>15.6f} "
                  f"{s['carbon_gco2']['mean']:>18.10f} {complexity:<12}")
        print()

    # --- Save Results ---
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "environment": env.to_dict(),
        "config": {"scales": SCALES, "measured_runs": MEASURED_RUNS},
        "statistics": {
            scale: {algo: stats.summarize() for algo, stats in scale_data.items()}
            for scale, scale_data in all_results.items()
        },
    }
    output_path = os.path.join(RESULTS_DIR, "03_sorting_algorithms.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
