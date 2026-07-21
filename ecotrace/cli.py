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
        return "1.4.2"


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
    eco = EcoTrace(region_code=args.region, check_updates=False, quiet=False,
                   run_label=getattr(args, 'label', None))

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
    """Exports session data to JSON or CSV format with filters."""
    _print_banner()

    if args.format not in ("json", "csv"):
        print(f"[ERROR] Unsupported format: {args.format}")
        sys.exit(1)

    csv_path = getattr(args, "file", "ecotrace_log.csv")
    output_path = args.output

    # Default output path matches the chosen format
    if output_path is None:
        output_path = "ecotrace_report.json" if args.format == "json" else "ecotrace_export.csv"

    if args.format == "json":
        from ecotrace.core import EcoTrace
        eco = EcoTrace(check_updates=False, quiet=True)
        try:
            eco.export_json(output_path, csv_path=csv_path)
            print(f"[EXPORT] JSON report created successfully: {output_path}")
        except Exception as e:
            print(f"[ERROR] JSON export failed: {e}")
            sys.exit(1)
    elif args.format == "csv":
        if not os.path.isfile(csv_path):
            print(f"[ERROR] Log file not found: {csv_path}")
            sys.exit(1)

        try:
            filtered_rows = []
            headers = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                except StopIteration:
                    headers = []

                if headers:
                    func_idx = headers.index("Function") if "Function" in headers else -1
                    run_id_idx = headers.index("RunID") if "RunID" in headers else -1
                    run_lbl_idx = headers.index("RunLabel") if "RunLabel" in headers else -1

                    for row in reader:
                        # Apply filters
                        if args.run:
                            row_run_id = row[run_id_idx] if run_id_idx < len(row) else ""
                            row_run_lbl = row[run_lbl_idx] if run_lbl_idx < len(row) else ""
                            if args.run != row_run_id and args.run != row_run_lbl:
                                continue
                        if args.func:
                            row_func = row[func_idx] if func_idx < len(row) else ""
                            if args.func != row_func:
                                continue
                        filtered_rows.append(row)

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(filtered_rows)

            print(f"[EXPORT] Filtered CSV report written: {output_path} ({len(filtered_rows)} records)")
        except Exception as e:
            print(f"[ERROR] CSV export failed: {e}")
            sys.exit(1)


def _cmd_diff(args):
    """Compares carbon emissions of two runs side-by-side."""
    csv_path = args.file
    _print_banner()

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Log file not found: {csv_path}")
        sys.exit(1)

    # Aggregate data by RunID
    run_map = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    carbon = float(row.get("Carbon(gCO2)", 0))
                    duration = float(row.get("Duration(s)", 0))
                except (ValueError, TypeError):
                    continue

                run_id = row.get("RunID", "").strip() or "legacy"
                run_label = row.get("RunLabel", "").strip()
                date = row.get("Date", "")

                if run_id not in run_map:
                    run_map[run_id] = {
                        "run_id": run_id,
                        "label": run_label,
                        "date": date,
                        "count": 0,
                        "duration_s": 0.0,
                        "carbon_gco2": 0.0,
                    }
                r = run_map[run_id]
                r["count"] += 1
                r["duration_s"] += duration
                r["carbon_gco2"] += carbon
                if date > r["date"]:
                    r["date"] = date
    except Exception as e:
        print(f"[ERROR] CSV read error: {e}")
        sys.exit(1)

    if not run_map:
        print("[INFO] No runs found in log.")
        return

    sorted_runs = sorted(run_map.values(), key=lambda x: x["date"])

    run_id1 = None
    run_id2 = None

    if args.latest:
        if len(sorted_runs) < 2:
            print("[ERROR] At least 2 runs are required to perform a comparison.")
            sys.exit(1)
        run_id1 = sorted_runs[-2]["run_id"]
        run_id2 = sorted_runs[-1]["run_id"]
    else:
        if not args.run_ids or len(args.run_ids) != 2:
            print("[ERROR] Please specify exactly two Run IDs or use --latest.")
            sys.exit(1)
        run_id1, run_id2 = args.run_ids

    if run_id1 not in run_map:
        print(f"[ERROR] Run ID not found: {run_id1}")
        sys.exit(1)
    if run_id2 not in run_map:
        print(f"[ERROR] Run ID not found: {run_id2}")
        sys.exit(1)

    r1 = run_map[run_id1]
    r2 = run_map[run_id2]

    diff_carbon = r2["carbon_gco2"] - r1["carbon_gco2"]
    diff_duration = r2["duration_s"] - r1["duration_s"]
    diff_funcs = r2["count"] - r1["count"]

    pct_carbon = (diff_carbon / r1["carbon_gco2"] * 100) if r1["carbon_gco2"] > 0 else 0.0
    pct_duration = (diff_duration / r1["duration_s"] * 100) if r1["duration_s"] > 0 else 0.0
    pct_funcs = (diff_funcs / r1["count"] * 100) if r1["count"] > 0 else 0.0

    print("=" * 72)
    print("  EcoTrace — Run Comparison Report")
    print("=" * 72)
    print(f"  {'Metric':<15} | {'Base (Run 1)':<24} | {'Target (Run 2)':<24}")
    print(f"  {'':<15} | {run_id1:<24} | {run_id2:<24}")
    print(f"  {'Label':<15} | {r1['label']:<24} | {r2['label']:<24}")
    print(f"  {'Date':<15} | {r1['date']:<24} | {r2['date']:<24}")
    print("-" * 72)
    
    sign_c = "+" if diff_carbon >= 0 else ""
    sign_d = "+" if diff_duration >= 0 else ""
    sign_f = "+" if diff_funcs >= 0 else ""

    print(f"  {'Functions':<15} | {r1['count']:<24} | {r2['count']:<24}")
    print(f"  {'Delta (Funcs)':<15} | {sign_f}{diff_funcs} ({sign_f}{pct_funcs:.1f}%)")
    print("-" * 72)
    print(f"  {'Duration':<15} | {r1['duration_s']:<20.4f} s | {r2['duration_s']:<20.4f} s")
    print(f"  {'Delta (Time)':<15} | {sign_d}{diff_duration:.4f} s ({sign_d}{pct_duration:.1f}%)")
    print("-" * 72)
    print(f"  {'Carbon (CO2)':<15} | {r1['carbon_gco2']:<20.8f} g | {r2['carbon_gco2']:<20.8f} g")
    print(f"  {'Delta (CO2)':<15} | {sign_c}{diff_carbon:.8f} g ({sign_c}{pct_carbon:.1f}%)")
    print("=" * 72)


def _cmd_clean(args):
    """Trims the CSV audit log by run count or date, creating a backup first."""
    csv_path = args.file
    _print_banner()

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Log file not found: {csv_path}")
        sys.exit(1)

    import shutil
    backup_path = csv_path + ".bak"
    try:
        shutil.copy(csv_path, backup_path)
        print(f"[CLEAN] Backup created: {backup_path}")
    except Exception as e:
        print(f"[ERROR] Could not create backup file: {e}")
        sys.exit(1)

    try:
        rows = []
        headers = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"[ERROR] CSV read failed: {e}")
        sys.exit(1)

    if not rows:
        print("[INFO] Log file is empty. Nothing to clean.")
        return

    original_count = len(rows)

    # Filter 1: --before DATE
    if args.before:
        filtered_rows = []
        for row in rows:
            date_str = row.get("Date", "")
            cmp_len = len(args.before)
            if date_str[:cmp_len] < args.before:
                continue
            filtered_rows.append(row)
        rows = filtered_rows

    # Filter 2: --keep-runs N
    if args.keep_runs is not None:
        if args.keep_runs <= 0:
            print("[ERROR] --keep-runs must be a positive integer.")
            sys.exit(1)

        run_dates = {}
        for row in rows:
            run_id = row.get("RunID", "").strip() or "legacy"
            date = row.get("Date", "")
            if run_id not in run_dates or date > run_dates[run_id]:
                run_dates[run_id] = date

        sorted_runs = sorted(run_dates.keys(), key=lambda r: run_dates[r])
        kept_runs = set(sorted_runs[-args.keep_runs:])

        filtered_rows = []
        for row in rows:
            run_id = row.get("RunID", "").strip() or "legacy"
            if run_id in kept_runs:
                filtered_rows.append(row)
        rows = filtered_rows

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers or [])
            writer.writeheader()
            writer.writerows(rows)
        print(f"[CLEAN] Trimmed {original_count - len(rows)} entries. {len(rows)} remaining.")
    except Exception as e:
        print(f"[ERROR] Failed to write trimmed CSV: {e}")
        sys.exit(1)


def _cmd_reset(args):
    """Deletes the CSV log file entirely after confirmation."""
    csv_path = args.file
    _print_banner()

    if not os.path.exists(csv_path):
        print(f"[RESET] Log file does not exist: {csv_path}")
        return

    if not args.yes:
        print("WARNING: This will permanently delete the carbon emission log file!")
        try:
            confirm = input("Are you sure you want to proceed? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nReset cancelled.")
            sys.exit(1)
        if confirm != "y":
            print("Reset cancelled.")
            return

    try:
        os.remove(csv_path)
        print(f"[RESET] Successfully deleted {csv_path}")
    except Exception as e:
        print(f"[ERROR] Failed to delete log file: {e}")
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
        if isinstance(result, dict):
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
# Subcommand: gate (v1.0)
# =============================================================================
# CI/CD carbon budget enforcement. The library decides pass/fail based on
# accumulated emissions. The pipeline acts on the exit code.
# This is the library's rule — not the IDE's, not the user's guess.

def _cmd_gate(args):
    """Enforces a carbon budget against the CSV audit log.

    Reads ``ecotrace_log.csv``, sums total carbon emissions, and compares
    against the specified budget. Returns exit code 0 if within budget,
    exit code 1 if exceeded.

    Designed for CI/CD pipeline integration::

        # GitHub Actions example
        - name: Carbon Gate
          run: ecotrace gate --budget 10.0

    Args:
        args: Parsed argparse namespace with ``budget`` and ``file`` options.
    """
    csv_path = args.file
    budget = args.budget
    _print_banner()

    print(f"[GATE] Budget    : {budget:.6f} gCO2")
    print(f"[GATE] Log file  : {csv_path}")
    print()

    # --- Parse CSV audit log for total emissions ----------------------------
    total_carbon = 0.0
    measurement_count = 0

    if not os.path.isfile(csv_path):
        print(f"[GATE] No log file found: {csv_path}")
        print("[GATE] Result: PASS (no emissions recorded)")
        sys.exit(0)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    total_carbon += float(row.get("Carbon(gCO2)", 0))
                    measurement_count += 1
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        print(f"[ERROR] CSV read failed: {e}")
        sys.exit(1)

    # --- Budget evaluation --------------------------------------------------
    # The library produces the verdict. The pipeline acts on exit code.
    used_pct = (total_carbon / budget) * 100 if budget > 0 else 0

    print("=" * 55)
    print("  EcoTrace — Carbon Gate Report")
    print("=" * 55)
    print(f"  Measurements   : {measurement_count}")
    print(f"  Total Carbon   : {total_carbon:.8f} gCO2")
    print(f"  Budget         : {budget:.6f} gCO2")
    print(f"  Usage          : {used_pct:.1f}%")
    print("-" * 55)

    if total_carbon > budget:
        print(f"  Result: FAIL — Budget exceeded by {total_carbon - budget:.6f} gCO2")
        print("=" * 55)
        sys.exit(1)
    else:
        remaining = budget - total_carbon
        print(f"  Result: PASS — {remaining:.6f} gCO2 remaining")
        print("=" * 55)
        sys.exit(0)


# =============================================================================
# Subcommand: history (v1.3.0)
# =============================================================================
# Groups CSV measurements by RunID and prints a per-run summary table.

def _cmd_history(args):
    """Prints a per-run carbon summary grouped by RunID.

    Reads the audit CSV and aggregates emissions by the RunID column
    (added in v1.3.0). Legacy rows without a RunID are grouped together
    under the label 'legacy'.

    Args:
        args: Parsed argparse namespace with optional ``file`` and ``runs`` options.
    """
    csv_path = args.file
    max_runs = args.runs
    _print_banner()

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Log file not found: {csv_path}")
        print("[INFO]  Run 'ecotrace run <script.py>' first to create a session.")
        sys.exit(1)

    run_map = {}  # run_id -> {label, date, count, duration_s, carbon_gco2}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    carbon = float(row.get("Carbon(gCO2)", 0))
                    duration = float(row.get("Duration(s)", 0))
                except (ValueError, TypeError):
                    continue

                run_id = row.get("RunID", "").strip() or "legacy"
                run_label = row.get("RunLabel", "").strip()
                date = row.get("Date", "")

                if run_id not in run_map:
                    run_map[run_id] = {
                        "label": run_label,
                        "date": date,
                        "count": 0,
                        "duration_s": 0.0,
                        "carbon_gco2": 0.0,
                    }
                r = run_map[run_id]
                r["count"] += 1
                r["duration_s"] += duration
                r["carbon_gco2"] += carbon
                if date > r["date"]:
                    r["date"] = date
    except Exception as e:
        print(f"[ERROR] CSV read error: {e}")
        sys.exit(1)

    if not run_map:
        print("[INFO] No measurements found.")
        return

    # Sort newest first, optionally limit
    runs = sorted(run_map.items(), key=lambda x: x[1]["date"], reverse=True)
    if max_runs:
        runs = runs[:max_runs]

    print("=" * 72)
    print("  EcoTrace — Run History")
    print("=" * 72)
    print(f"  {'Run ID':<14} {'Label':<18} {'Date':<20} {'Funcs':>5} {'Duration(s)':>12} {'Carbon(gCO2)':>14}")
    print("  " + "-" * 68)
    for run_id, r in runs:
        label = r["label"][:16] if r["label"] else ""
        print(f"  {run_id:<14} {label:<18} {r['date']:<20} {r['count']:>5} {r['duration_s']:>12.4f} {r['carbon_gco2']:>14.8f}")
    print("=" * 72)
    total = sum(r["carbon_gco2"] for _, r in runs)
    print(f"  Showing {len(runs)} run(s) | Total Carbon: {total:.8f} gCO2")
    print("=" * 72)


# =============================================================================
# Subcommand: trends (v1.3.0)
# =============================================================================
# Shows carbon per run as an ASCII sparkline for quick trend spotting.

def _cmd_trends(args):
    """Displays an ASCII carbon-per-run trend chart for the last N runs.

    Reads the audit CSV, groups by RunID, and renders a minimal ASCII
    bar chart so users can spot whether their code is getting greener
    over time without opening a browser.

    Args:
        args: Parsed argparse namespace with optional ``file`` and ``runs`` options.
    """
    csv_path = args.file
    max_runs = args.runs
    _print_banner()

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Log file not found: {csv_path}")
        sys.exit(1)

    run_map = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    carbon = float(row.get("Carbon(gCO2)", 0))
                except (ValueError, TypeError):
                    continue
                run_id = row.get("RunID", "").strip() or "legacy"
                run_label = row.get("RunLabel", "").strip()
                date = row.get("Date", "")
                if run_id not in run_map:
                    run_map[run_id] = {"label": run_label, "date": date, "carbon": 0.0}
                run_map[run_id]["carbon"] += carbon
                if date > run_map[run_id]["date"]:
                    run_map[run_id]["date"] = date
    except Exception as e:
        print(f"[ERROR] CSV read error: {e}")
        sys.exit(1)

    runs = sorted(run_map.items(), key=lambda x: x[1]["date"])[-max_runs:]
    if not runs:
        print("[INFO] No runs found.")
        return

    # ASCII bar chart — scale to terminal width (max 40 chars wide)
    BAR_WIDTH = 40
    max_c = max(r["carbon"] for _, r in runs) or 1.0
    print("=" * 60)
    print("  EcoTrace — Carbon Trends (oldest -> newest)")
    print("=" * 60)
    prev_carbon = None
    for run_id, r in runs:
        bar_len = max(1, int((r["carbon"] / max_c) * BAR_WIDTH))
        bar = "#" * bar_len
        trend = ""
        if prev_carbon is not None:
            if r["carbon"] < prev_carbon:
                trend = " (DOWN)"
            elif r["carbon"] > prev_carbon:
                trend = " (UP)"
        label_str = f" [{r['label']}]" if r["label"] else ""
        print(f"  {run_id}{label_str}")
        print(f"  {bar:<{BAR_WIDTH}}  {r['carbon']:.6f} gCO2{trend}")
        print()
        prev_carbon = r["carbon"]
    print("=" * 60)


# =============================================================================
# Subcommand: dashboard (v1.3.0)
# =============================================================================
# Starts the local HTTP dashboard server.




# =============================================================================
# Subcommand: optimize (v1.0.1)
# =============================================================================
# Connects to Google Gemini AI to analyze a specific function's source code
# and provide carbon-aware optimization suggestions. Called by the VS Code extension.

def _cmd_optimize(args):
    """Analyzes a function's source code using Gemini AI for energy optimizations."""
    file_path = args.file
    func_name = args.func
    region = args.region

    # Don't print banner here because VS Code reads stdout directly for HTML rendering
    # or just raw text.

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    if not os.path.isfile(file_path):
        print(f"Error: Source file not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading source file: {e}")
        sys.exit(1)

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
            import google.generativeai as genai

        configure_fn = getattr(genai, "configure", None)
        model_cls = getattr(genai, "GenerativeModel", None)
        if not configure_fn or not model_cls:
            print("[ERROR] google-generativeai module is missing required components.")
            return
        configure_fn(api_key=api_key)
        model = model_cls('gemini-1.5-flash')
        
        prompt = (
            f"You are an expert Python performance and sustainability engineer. "
            f"Analyze the function '{func_name}' in the following Python code for energy efficiency and carbon emissions. "
            f"Provide concrete, actionable code changes to reduce CPU usage and execution time. "
            f"Keep your answer concise, professional, and format it using Markdown. Do not use emojis.\n\n"
            f"```python\n{source_code}\n```"
        )
        
        response = model.generate_content(prompt)
        print(response.text)
        sys.exit(0)
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        sys.exit(1)



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
    run_parser.add_argument("-l", "--label", default=None, help="Human-readable label for this run (stored in CSV)")

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
        help="Export session data to JSON or CSV format",
        description="Export hardware info and measurement history as JSON, or filtered CSV."
    )
    export_parser.add_argument("--json", dest="format", action="store_const", const="json", default="json",
                               help="Export in JSON format (default)")
    export_parser.add_argument("--csv", dest="format", action="store_const", const="csv",
                               help="Export in CSV format")
    export_parser.add_argument("-f", "--file", default="ecotrace_log.csv", help="Path to source CSV log file")
    export_parser.add_argument("--run", default=None, help="Filter export by Run ID or Run Label")
    export_parser.add_argument("--func", default=None, help="Filter export by function name")
    export_parser.add_argument("-o", "--output", default=None, help="Output file path (default: based on format)")

    # --- benchmark ---
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Measure EcoTrace's own overhead cost",
        description="Run a controlled workload with and without EcoTrace and report the difference."
    )
    benchmark_parser.add_argument("-n", "--iterations", type=int, default=500_000,
                                  help="Benchmark iteration count (default: 500000)")

    # --- gate (v1.0) ---
    gate_parser = subparsers.add_parser(
        "gate",
        help="CI/CD carbon budget gate (exit 1 if budget exceeded)",
        description="Check total emissions against a carbon budget. Returns exit code 1 if exceeded."
    )
    gate_parser.add_argument("-b", "--budget", type=float, required=True,
                             help="Carbon budget threshold in gCO2")
    gate_parser.add_argument("-r", "--region", default="GLOBAL",
                             help="ISO region code for carbon intensity (default: GLOBAL)")
    gate_parser.add_argument("-f", "--file", default="ecotrace_log.csv",
                             help="Path to CSV log file (default: ecotrace_log.csv)")

    # --- history (v1.3.0) ---
    history_parser = subparsers.add_parser(
        "history",
        help="Show per-run carbon summary grouped by RunID",
        description="Groups the audit CSV by RunID and prints a per-run carbon table."
    )
    history_parser.add_argument("-f", "--file", default="ecotrace_log.csv",
                                help="Path to CSV log file (default: ecotrace_log.csv)")
    history_parser.add_argument("-n", "--runs", type=int, default=None,
                                help="Maximum number of recent runs to show (default: all)")

    # --- trends (v1.3.0) ---
    trends_parser = subparsers.add_parser(
        "trends",
        help="ASCII carbon-per-run trend chart",
        description="Shows an ASCII bar chart of carbon emissions across the last N runs."
    )
    trends_parser.add_argument("-f", "--file", default="ecotrace_log.csv",
                               help="Path to CSV log file (default: ecotrace_log.csv)")
    trends_parser.add_argument("-n", "--runs", type=int, default=10,
                               help="Number of most recent runs to show (default: 10)")



    # --- optimize (v1.0.1) ---
    optimize_parser = subparsers.add_parser(
        "optimize",
        help="Analyze a function using AI for carbon optimization",
        description="Reads a source file and asks Gemini AI for energy optimizations on a specific function."
    )
    optimize_parser.add_argument("file", help="Python source file to analyze")
    optimize_parser.add_argument("--func", required=True, help="Name of the function to optimize")
    optimize_parser.add_argument("--region", default="GLOBAL", help="ISO region code for context")

    # --- diff ---
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare two runs side-by-side",
        description="Compare carbon emissions and duration between two runs."
    )
    diff_parser.add_argument("run_ids", nargs="*", help="Exactly two Run IDs to compare")
    diff_parser.add_argument("--latest", action="store_true", help="Compare the latest two runs")
    diff_parser.add_argument("-f", "--file", default="ecotrace_log.csv", help="Path to CSV log file")

    # --- clean ---
    clean_parser = subparsers.add_parser(
        "clean",
        help="Trim the CSV log file by date or run count",
        description="Rotate/cleanup CSV logs by removing old runs."
    )
    clean_parser.add_argument("--keep-runs", type=int, default=None, help="Number of latest runs to keep")
    clean_parser.add_argument("--before", default=None, help="Remove entries older than YYYY-MM-DD")
    clean_parser.add_argument("-f", "--file", default="ecotrace_log.csv", help="Path to CSV log file")

    # --- reset ---
    reset_parser = subparsers.add_parser(
        "reset",
        help="Delete the CSV log file entirely",
        description="Delete ecotrace_log.csv after confirmation."
    )
    reset_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    reset_parser.add_argument("-f", "--file", default="ecotrace_log.csv", help="Path to CSV log file")

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
        "gate": _cmd_gate,
        "optimize": _cmd_optimize,
        "history": _cmd_history,
        "trends": _cmd_trends,
        "diff": _cmd_diff,
        "clean": _cmd_clean,
        "reset": _cmd_reset,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
