"""
Benchmark Runner
=================
Standardized harness for executing benchmarks with configurable repetitions,
warm-up rounds, statistical analysis, and automatic report generation.
"""

import os
import sys
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, Any, List, Optional

# Ensure local ecotrace package is resolvable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from .environment import EnvironmentSnapshot
from .statistics import BenchmarkStatistics, mean, remove_outliers_iqr


@dataclass
class BenchmarkResult:
    """Holds the complete result of a single benchmark invocation.

    Fields are populated by the BenchmarkRunner after each run.
    """
    label: str
    run_index: int
    duration_s: float
    carbon_gco2: float
    energy_wh: float
    avg_cpu_pct: float
    extra_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BenchmarkRunner:
    """Orchestrates benchmark execution with scientific rigor.

    Features:
        - Configurable warm-up iterations (discarded from analysis)
        - Configurable measured iterations with optional cooldown
        - Automatic EcoTrace integration for energy/carbon measurement
        - Statistical analysis and comparison across benchmarks
        - JSON export for reproducibility

    Usage::

        runner = BenchmarkRunner(
            suite_name="DataEngine-Benchmark",
            region_code="TR",
            warmup_runs=2,
            measured_runs=10,
            cooldown_s=1.0,
        )

        runner.register("pandas", run_pandas_pipeline)
        runner.register("polars", run_polars_pipeline)

        results = runner.execute_all()
        runner.save_results("results/benchmark_output.json")
    """

    def __init__(
        self,
        suite_name: str = "EcoTrace Benchmark",
        region_code: str = "GLOBAL",
        warmup_runs: int = 2,
        measured_runs: int = 10,
        cooldown_s: float = 0.5,
        output_dir: str = "results",
    ):
        self.suite_name = suite_name
        self.region_code = region_code
        self.warmup_runs = warmup_runs
        self.measured_runs = measured_runs
        self.cooldown_s = cooldown_s
        self.output_dir = output_dir

        self._benchmarks: Dict[str, Callable] = {}
        self._stats: Dict[str, BenchmarkStatistics] = {}
        self._results: Dict[str, List[BenchmarkResult]] = {}
        self._environment: Optional[EnvironmentSnapshot] = None

    def register(self, label: str, func: Callable, **static_kwargs) -> None:
        """Registers a benchmark function to be executed.

        Args:
            label: Human-readable name for this benchmark variant.
            func: Callable that performs the workload. Should accept no arguments
                  (or use functools.partial / lambda wrappers).
            **static_kwargs: Additional keyword arguments passed to func on every call.
        """
        if static_kwargs:
            import functools
            func = functools.partial(func, **static_kwargs)
        self._benchmarks[label] = func

    def execute_all(self) -> Dict[str, List[BenchmarkResult]]:
        """Executes all registered benchmarks and returns structured results.

        Returns:
            Dictionary mapping benchmark labels to lists of BenchmarkResult objects.
        """
        from ecotrace import EcoTrace

        self._environment = EnvironmentSnapshot()
        print(f"\n{'=' * 70}")
        print(f"  {self.suite_name}")
        print(f"  {self.measured_runs} measured runs | {self.warmup_runs} warm-up | "
              f"{self.cooldown_s}s cooldown")
        print(f"{'=' * 70}\n")

        eco = EcoTrace(
            region_code=self.region_code,
            check_updates=False,
            run_label=self.suite_name,
            session_summary=False,
        )

        for label, func in self._benchmarks.items():
            stats = BenchmarkStatistics(label)
            results: List[BenchmarkResult] = []

            # --- Warm-up Phase -----------------------------------------------
            if self.warmup_runs > 0:
                print(f"  [{label}] Warming up ({self.warmup_runs} runs)...")
                for _ in range(self.warmup_runs):
                    func()
                    time.sleep(self.cooldown_s)

            # --- Measured Phase ----------------------------------------------
            print(f"  [{label}] Measuring ({self.measured_runs} runs)...")
            for i in range(self.measured_runs):
                carbon_before = eco.total_carbon
                energy_before = eco.total_energy_kwh

                with eco.track_block(f"{label}_run_{i}"):
                    t0 = time.perf_counter()
                    extra = func()
                    duration = time.perf_counter() - t0

                carbon_delta = eco.total_carbon - carbon_before
                energy_delta = eco.total_energy_kwh - energy_before

                # Get latest CPU average from EcoTrace session
                summary = eco.get_summary()
                avg_cpu = summary.get("hardware", {}).get("avg_cpu_pct", 0.0)

                extra_metrics = {}
                if isinstance(extra, dict):
                    extra_metrics = {k: float(v) for k, v in extra.items()
                                     if isinstance(v, (int, float))}

                result = BenchmarkResult(
                    label=label,
                    run_index=i,
                    duration_s=round(duration, 6),
                    carbon_gco2=round(carbon_delta, 10),
                    energy_wh=round(energy_delta, 10),
                    avg_cpu_pct=0.0,
                    extra_metrics=extra_metrics,
                )
                results.append(result)
                stats.add_run(
                    duration=duration,
                    carbon_gco2=carbon_delta,
                    energy_wh=energy_delta,
                    avg_cpu=0.0,
                    **extra_metrics,
                )

                # Progress indicator
                sys.stdout.write(f"\r    Run {i + 1}/{self.measured_runs} -- "
                                 f"{duration:.4f}s, {carbon_delta:.8f} gCO2")
                sys.stdout.flush()

                if self.cooldown_s > 0 and i < self.measured_runs - 1:
                    time.sleep(self.cooldown_s)

            print()  # newline after progress bar
            self._stats[label] = stats
            self._results[label] = results

        print(f"\n{'=' * 70}")
        print(f"  All benchmarks completed.")
        print(f"{'=' * 70}\n")

        return self._results

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Returns statistical summaries for all executed benchmarks."""
        return {label: stats.summarize() for label, stats in self._stats.items()}

    def get_comparison(self, baseline: str, challenger: str) -> Dict[str, Any]:
        """Compares two benchmarks statistically.

        Args:
            baseline: Label of the baseline benchmark.
            challenger: Label of the challenger benchmark.

        Returns:
            Comparison dict with speedup, carbon savings, and significance tests.
        """
        if baseline not in self._stats or challenger not in self._stats:
            raise ValueError(f"Both '{baseline}' and '{challenger}' must be executed first.")
        return self._stats[baseline].compare(self._stats[challenger])

    def save_results(self, filepath: Optional[str] = None) -> str:
        """Saves the complete benchmark results to a JSON file.

        Args:
            filepath: Output path. Defaults to {output_dir}/{suite_name}_results.json.

        Returns:
            Absolute path to the saved file.
        """
        if filepath is None:
            safe_name = self.suite_name.lower().replace(" ", "_").replace("-", "_")
            filepath = os.path.join(self.output_dir, f"{safe_name}_results.json")

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        output = {
            "suite": self.suite_name,
            "config": {
                "region_code": self.region_code,
                "warmup_runs": self.warmup_runs,
                "measured_runs": self.measured_runs,
                "cooldown_s": self.cooldown_s,
            },
            "environment": self._environment.to_dict() if self._environment else None,
            "statistics": self.get_statistics(),
            "raw_results": {
                label: [r.to_dict() for r in results]
                for label, results in self._results.items()
            },
        }

        # Add pairwise comparisons if we have 2+ benchmarks
        labels = list(self._stats.keys())
        if len(labels) >= 2:
            comparisons = []
            for i, base in enumerate(labels):
                for challenger in labels[i + 1:]:
                    try:
                        comparisons.append(self.get_comparison(base, challenger))
                    except Exception:
                        pass
            output["comparisons"] = comparisons

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"  Results saved to: {os.path.abspath(filepath)}")
        return os.path.abspath(filepath)

    def print_summary_table(self) -> None:
        """Prints a formatted comparison table to stdout."""
        stats = self.get_statistics()
        if not stats:
            print("  No benchmark results to display.")
            return

        print(f"\n{'-' * 80}")
        print(f"  {'Benchmark':<25} {'Duration (s)':<18} {'Carbon (gCO2)':<18} {'CV%':<8}")
        print(f"{'-' * 80}")

        for label, s in stats.items():
            dur = s["duration_s"]
            carbon = s["carbon_gco2"]
            print(f"  {label:<25} {dur['mean']:<18.6f} {carbon['mean']:<18.8f} {dur['cv_pct']:<8.2f}")

        print(f"{'-' * 80}")

        # Pairwise comparisons
        labels = list(stats.keys())
        if len(labels) >= 2:
            print(f"\n  Pairwise Comparisons:")
            print(f"  {'-' * 60}")
            for i, base in enumerate(labels):
                for challenger in labels[i + 1:]:
                    try:
                        comp = self.get_comparison(base, challenger)
                        sig = "[OK] SIGNIFICANT" if comp["duration_test"]["significant_at_05"] else "[X] Not significant"
                        print(f"  {base} vs {challenger}: "
                              f"{comp['speedup_ratio']:.2f}x speedup, "
                              f"{comp['carbon_reduction_pct']:.1f}% carbon reduction "
                              f"({sig}, p={comp['duration_test']['p_value_approx']:.4f})")
                    except Exception:
                        pass
            print()
