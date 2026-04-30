"""EcoTrace CLI — Terminal interface for carbon-aware script profiling.

Provides four subcommands for headless carbon instrumentation without
modifying the target source code:

    ecotrace run <script.py>     Run a script under full carbon monitoring
    ecotrace analyze             Summarize existing CSV audit logs
    ecotrace export --json       Export session data to machine-readable JSON
    ecotrace benchmark           Measure EcoTrace's own overhead

Design constraints:
    - Zero external dependencies (argparse + runpy + json from stdlib)
    - Must never crash with ugly tracebacks — all commands are fail-safe
    - ``runpy.run_path`` keeps us in the same process so psutil isolation works
"""

import argparse
import sys
import os
import time
import csv
import json
import runpy
from datetime import datetime


# --- Version & Branding ------------------------------------------------------
# Lazy import to avoid circular dependency with __init__.py
def _get_version():
    """Resolves the current package version without triggering heavy imports."""
    try:
        from ecotrace import __version__
        return __version__
    except ImportError:
        return "0.9.0"


# --- CLI Banner --------------------------------------------------------------
# First impression matters. This prints once at the start of every CLI session
# so the user immediately knows which version and mode they're running.
# NOTE: ASCII-only characters to avoid cp1254/cp1252 encoding errors on Windows.
BANNER = """
============================================
  EcoTrace - Carbon Profiler CLI  v{ver}
============================================
""".strip()


def _print_banner():
    """Displays the CLI session banner with current version."""
    ver = _get_version()
    print(BANNER.format(ver=ver))
    print()


# =============================================================================
# Subcommand: run
# =============================================================================
# Core philosophy: wrap any script in a carbon monitoring session WITHOUT
# touching the user's source code. We use runpy.run_path() instead of
# subprocess so that psutil.Process() captures the SAME process tree.

def _cmd_run(args):
    """Executes a Python script under full EcoTrace instrumentation.

    Uses ``runpy.run_path`` to run the target script in the current process,
    preserving psutil process-scoped isolation. After execution, prints a
    carbon summary and optionally exports to JSON.

    Args:
        args: Parsed argparse namespace containing ``script`` path and
            optional ``region``, ``output`` parameters.
    """
    script_path = args.script

    if not os.path.isfile(script_path):
        print(f"[ERROR] File not found: {script_path}")
        sys.exit(1)

    if not script_path.endswith(".py"):
        print(f"[ERROR] Only Python files are supported: {script_path}")
        sys.exit(1)

    _print_banner()
    print(f"[RUN] Target: {os.path.abspath(script_path)}")
    print(f"[RUN] Region: {args.region}")
    print()

    # --- EcoTrace Engine Initialization ---
    # check_updates=False: Auto-update prompts are unnecessary in CLI mode.
    # quiet=False: User should see the hardware detection output.
    from ecotrace.core import EcoTrace
    eco = EcoTrace(region_code=args.region, check_updates=False, quiet=False)

    # --- Script Execution Under Monitoring ---
    # Rewrite sys.argv from the target script's perspective so it can
    # parse its own arguments correctly via argparse or sys.argv.
    original_argv = sys.argv[:]
    sys.argv = [script_path] + args.script_args

    session_start = time.perf_counter()
    energy_start = eco.hardware.get_cpu_energy_j()
    exit_code = 0

    try:
        # CPU monitoring context wraps the entire script execution
        with eco.cpu_monitor():
            if eco.gpu_info:
                with eco.gpu_monitor():
                    runpy.run_path(script_path, run_name="__main__")
            else:
                runpy.run_path(script_path, run_name="__main__")
    except SystemExit as e:
        # Scripts may call sys.exit() — capture the exit code, don't crash
        exit_code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user (Ctrl+C).")
        exit_code = 130
    except Exception as e:
        print(f"\n[ERROR] Script error: {e}")
        exit_code = 1
    finally:
        sys.argv = original_argv

    session_end = time.perf_counter()
    energy_end = eco.hardware.get_cpu_energy_j()
    session_duration = session_end - session_start

    # --- Post-Execution Carbon Summary ---
    # Calculate total carbon from the monitoring session
    try:
        avg_cpu = eco._get_avg_cpu_in_range(session_start, session_end)
        
        energy_delta_j = None
        if energy_start is not None and energy_end is not None:
            energy_delta_j = max(0.0, energy_end - energy_start)
            
        carbon_emitted = eco._compute_carbon(eco.cpu_info['tdp'], avg_cpu, session_duration, energy_delta_j=energy_delta_j)

        # Accumulate into the CSV audit log
        script_name = os.path.basename(script_path)
        eco._accumulate_carbon(carbon_emitted, f"cli::{script_name}", session_duration, avg_cpu)

        # Print the summary table
        _print_summary_table(script_path, session_duration, avg_cpu, carbon_emitted, eco)

    except Exception as e:
        print(f"[WARNING] Carbon calculation failed: {e}")

    # --- Optional JSON Export ---
    if args.output:
        try:
            eco.export_json(args.output)
            print(f"\n[EXPORT] JSON report written: {args.output}")
        except Exception as e:
            print(f"[WARNING] JSON export failed: {e}")

    sys.exit(exit_code)


def _print_summary_table(script_path, duration, avg_cpu, carbon, eco):
    """Renders a formatted carbon summary table to the terminal.

    Args:
        script_path: Path to the executed script.
        duration: Total execution time in seconds.
        avg_cpu: Average CPU utilization percentage.
        carbon: Total carbon emissions in gCO2.
        eco: EcoTrace instance for hardware metadata.
    """
    print()
    print("=" * 55)
    print("  EcoTrace - Carbon Summary Report")
    print("=" * 55)
    print(f"  Script         : {os.path.basename(script_path)}")
    print(f"  Duration       : {duration:.4f} seconds")
    print(f"  Avg. CPU       : {avg_cpu:.1f}%")
    print(f"  Carbon Emitted : {carbon:.8f} gCO2")
    print(f"  Region         : {eco.region_code} ({eco.carbon_intensity} gCO2/kWh)")
    print(f"  Processor      : {eco.cpu_info['brand']}")
    print(f"  TDP            : {eco.cpu_info['tdp']}W")

    if eco.gpu_info:
        print(f"  GPU            : {eco.gpu_info['brand']}")

    print(f"  Cumulative CO2 : {eco.total_carbon:.8f} gCO2")
    print("=" * 55)


# =============================================================================
# Subcommand: analyze
# =============================================================================
# Reads the existing ecotrace_log.csv audit trail and prints a quick summary.
# No EcoTrace initialization needed — pure file I/O.

def _cmd_analyze(args):
    """Parses the CSV audit log and displays a terminal summary.

    Reads ``ecotrace_log.csv`` from the current working directory,
    aggregates carbon emissions per function, and prints a ranked table
    showing the top emitters.

    Args:
        args: Parsed argparse namespace containing optional ``file`` path.
    """
    csv_path = args.file
    _print_banner()

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Log file not found: {csv_path}")
        print("[INFO]  Run 'ecotrace run <script.py>' first to create a session.")
        sys.exit(1)

    try:
        rows = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"[ERROR] CSV read error: {e}")
        sys.exit(1)

    if not rows:
        print("[INFO] Log file is empty — no measurements recorded yet.")
        return

    # --- Aggregate per function ---
    func_stats = {}
    total_carbon = 0.0
    total_duration = 0.0

    for row in rows:
        func_name = row.get("Function", "unknown")
        try:
            carbon = float(row.get("Carbon(gCO2)", 0))
            duration = float(row.get("Duration(s)", 0))
        except (ValueError, TypeError):
            continue

        total_carbon += carbon
        total_duration += duration

        if func_name not in func_stats:
            func_stats[func_name] = {"carbon": 0.0, "duration": 0.0, "calls": 0}

        func_stats[func_name]["carbon"] += carbon
        func_stats[func_name]["duration"] += duration
        func_stats[func_name]["calls"] += 1

    # --- Print summary ---
    print("=" * 60)
    print("  EcoTrace - CSV Analysis Report")
    print("=" * 60)
    print(f"  File           : {csv_path}")
    print(f"  Total Records  : {len(rows)}")
    print(f"  Total Duration : {total_duration:.4f} seconds")
    print(f"  Total Carbon   : {total_carbon:.8f} gCO2")
    print("-" * 60)

    # Sort by carbon (highest first), show top 10
    sorted_funcs = sorted(func_stats.items(), key=lambda x: x[1]["carbon"], reverse=True)

    print(f"  {'Function':<30} {'Calls':>5} {'CO2 (gCO2)':>14} {'Time (s)':>10}")
    print("  " + "-" * 56)

    for func_name, stats in sorted_funcs[:10]:
        print(f"  {func_name:<30} {stats['calls']:>5} {stats['carbon']:>14.8f} {stats['duration']:>10.4f}")

    if len(sorted_funcs) > 10:
        print(f"  ... and {len(sorted_funcs) - 10} more functions")

    print("=" * 60)


# =============================================================================
# Subcommand: export
# =============================================================================
# Bridges the gap between CSV logs and machine-readable output.
# VS Code extension will consume this JSON for its sidebar dashboard.

def _cmd_export(args):
    """Exports session data to JSON format for external tool consumption.

    Creates a structured JSON file containing hardware metadata,
    measurement history, and aggregate statistics.

    Args:
        args: Parsed argparse namespace with ``output`` and ``format`` options.
    """
    _print_banner()

    if args.format != "json":
        print(f"[ERROR] Unsupported format: {args.format}")
        print("[INFO]  Currently only JSON is supported: ecotrace export --json")
        sys.exit(1)

    output_path = args.output

    # Initialize EcoTrace quietly just for hardware metadata
    from ecotrace.core import EcoTrace
    eco = EcoTrace(check_updates=False, quiet=True)

    try:
        eco.export_json(output_path)
        print(f"[EXPORT] JSON report created successfully: {output_path}")
    except Exception as e:
        print(f"[ERROR] JSON export failed: {e}")
        sys.exit(1)


# =============================================================================
# Subcommand: benchmark
# =============================================================================
# Self-diagnostic tool: measures EcoTrace's own CPU overhead.
# Critical for proving "negligible overhead" claim in the README.

def _cmd_benchmark(args):
    """Measures EcoTrace's instrumentation overhead as a percentage of CPU time.

    Runs a controlled workload twice — once without monitoring (baseline)
    and once with full EcoTrace instrumentation — then reports the
    percentage difference as the overhead cost.

    Args:
        args: Parsed argparse namespace (no additional options needed).
    """
    _print_banner()
    print("[BENCHMARK] Starting EcoTrace overhead measurement...\n")

    iterations = args.iterations

    # --- Controlled Workload ---
    # Sufficiently CPU-heavy to produce measurable differences,
    # but short enough to not bore the user.
    def _workload():
        """Deterministic CPU-bound workload for consistent benchmarking."""
        total = 0
        for i in range(iterations):
            total += i * i
        return total

    # --- Phase 1: Baseline (without EcoTrace) ---
    print("[1/2] Baseline measurement (without EcoTrace)...")
    baseline_times = []
    for _ in range(3):
        start = time.perf_counter()
        _workload()
        baseline_times.append(time.perf_counter() - start)

    baseline_avg = sum(baseline_times) / len(baseline_times)

    # --- Phase 2: Instrumented (with EcoTrace) ---
    print("[2/2] Instrumented measurement (with EcoTrace)...")
    from ecotrace.core import EcoTrace
    eco = EcoTrace(check_updates=False, quiet=True)

    instrumented_times = []
    for _ in range(3):
        result = eco.measure(_workload)
        instrumented_times.append(result["duration"])

    instrumented_avg = sum(instrumented_times) / len(instrumented_times)

    # --- Results ---
    overhead_ms = (instrumented_avg - baseline_avg) * 1000
    overhead_pct = ((instrumented_avg - baseline_avg) / baseline_avg) * 100 if baseline_avg > 0 else 0

    print()
    print("=" * 55)
    print("  EcoTrace - Overhead Benchmark Results")
    print("=" * 55)
    print(f"  Iterations      : {iterations:,}")
    print(f"  Baseline (avg)  : {baseline_avg * 1000:.2f} ms")
    print(f"  EcoTrace (avg)  : {instrumented_avg * 1000:.2f} ms")
    print(f"  Overhead        : {overhead_ms:.2f} ms ({overhead_pct:.2f}%)")
    print("-" * 55)

    if overhead_pct < 1.0:
        print("  Result: Negligible overhead (<1%)")
    elif overhead_pct < 5.0:
        print("  Result: Low overhead (<5%)")
    else:
        print(f"  Result: Measurable overhead ({overhead_pct:.1f}%)")

    print("=" * 55)


# =============================================================================
# Argument Parser — CLI Entry Point
# =============================================================================
# Uses Python's built-in argparse to avoid adding click/typer dependencies.
# Each subcommand maps to a _cmd_* handler function above.

def main():
    """Main entry point for the ``ecotrace`` CLI command.

    Registered as a console script in ``pyproject.toml`` via::

        [project.scripts]
        ecotrace = "ecotrace.cli:main"

    Also accessible via ``python -m ecotrace``.
    """
    parser = argparse.ArgumentParser(
        prog="ecotrace",
        description="EcoTrace - Carbon-aware Python profiler CLI",
        epilog="Documentation: https://github.com/Zwony/ecotrace"
    )
    parser.add_argument(
        "--version", action="version",
        version=f"EcoTrace {_get_version()}"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available subcommands"
    )

    # --- run ---
    run_parser = subparsers.add_parser(
        "run",
        help="Run a Python script with carbon monitoring",
        description="Execute a target script under a full EcoTrace session."
    )
    run_parser.add_argument("script", help="Python file to execute (.py)")
    run_parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments for the script")
    run_parser.add_argument("-r", "--region", default="GLOBAL", help="ISO region code (default: GLOBAL)")
    run_parser.add_argument("-o", "--output", default=None, help="Write results to a JSON file")

    # --- analyze ---
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze existing CSV log file in the terminal",
        description="Read ecotrace_log.csv and display a per-function summary table."
    )
    analyze_parser.add_argument("-f", "--file", default="ecotrace_log.csv", help="Path to CSV log file")

    # --- export ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export session data to JSON format",
        description="Export hardware info and measurement history as JSON."
    )
    export_parser.add_argument("--json", dest="format", action="store_const", const="json", default="json",
                               help="Export in JSON format (default)")
    export_parser.add_argument("-o", "--output", default="ecotrace_report.json", help="Output file path")

    # --- benchmark ---
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Measure EcoTrace's own overhead cost",
        description="Run a controlled workload with and without EcoTrace and report the difference."
    )
    benchmark_parser.add_argument("-n", "--iterations", type=int, default=500_000,
                                  help="Benchmark iteration count (default: 500000)")

    # --- Parse & Dispatch ---
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Command dispatch table
    commands = {
        "run": _cmd_run,
        "analyze": _cmd_analyze,
        "export": _cmd_export,
        "benchmark": _cmd_benchmark,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
