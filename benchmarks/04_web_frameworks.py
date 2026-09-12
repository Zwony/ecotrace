"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 04: Web Frameworks
================================================================================
Compares the carbon cost per request of Flask, FastAPI, and Django
under identical synthetic HTTP load.
================================================================================
"""

import os
import sys
import time
import json
import threading
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ecotrace import EcoTrace
from benchmarks.framework import EnvironmentSnapshot, BenchmarkStatistics

# --- Configuration -----------------------------------------------------------
NUM_REQUESTS = 5000
CONCURRENCY = 10
FRAMEWORK_PORTS = {
    "flask": 8891,
    "fastapi": 8892,
}
WARMUP_REQUESTS = 500
MEASURED_RUNS = 3  # reduced from 5 for CPU feasibility
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Sample JSON payload for consistent responses
SAMPLE_RESPONSE = {
    "status": "ok",
    "data": {"id": 1, "name": "benchmark", "value": 42.0},
    "items": [{"x": i, "y": i * 2.5} for i in range(20)],
}


def _check_available(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


# =============================================================================
# Flask Application
# =============================================================================
def create_flask_app():
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/api/benchmark")
    def benchmark_endpoint():
        return jsonify(SAMPLE_RESPONSE)

    return app


def run_flask_server(port=8891):
    app = create_flask_app()
    app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


# =============================================================================
# FastAPI Application
# =============================================================================
def create_fastapi_app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()

    @app.get("/api/benchmark")
    async def benchmark_endpoint():
        return JSONResponse(content=SAMPLE_RESPONSE)

    return app


def run_fastapi_server(port=8892):
    import uvicorn
    app = create_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


# =============================================================================
# Load Generator (using urllib -- no external dependency)
# =============================================================================
def send_requests(url: str, count: int, concurrency: int = 10) -> dict:
    """Sends HTTP requests and measures throughput."""
    import urllib.request
    import urllib.error
    from concurrent.futures import ThreadPoolExecutor, as_completed

    latencies = []
    errors = 0

    def _single_request():
        try:
            t0 = time.perf_counter()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            return time.perf_counter() - t0
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_single_request) for _ in range(count)]
        for fut in as_completed(futures):
            latency = fut.result()
            if latency is not None:
                latencies.append(latency)
            else:
                errors += 1

    latencies.sort()
    n = len(latencies)
    total_time = sum(latencies) / concurrency if latencies else 0  # divide by concurrency for true rps
    return {
        "total_requests": count,
        "successful": n,
        "errors": errors,
        "rps": n / total_time if total_time > 0 else 0,
        "latency_mean_ms": (sum(latencies) / n * 1000) if n else 0,
        "latency_p50_ms": (latencies[n // 2] * 1000) if n else 0,
        "latency_p99_ms": (latencies[int(n * 0.99)] * 1000) if n else 0,
    }


def _wait_for_server(port, timeout=10):
    """Polls the server until it's ready."""
    import urllib.request
    import urllib.error
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/benchmark", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def benchmark_framework(name, server_fn, port, eco):
    """Benchmarks a single web framework."""
    stats = BenchmarkStatistics(name)
    url = f"http://127.0.0.1:{port}/api/benchmark"

    # Start server once in background daemon thread
    server_thread = threading.Thread(target=lambda: server_fn(port), daemon=True)
    server_thread.start()

    if not _wait_for_server(port):
        print(f"    [!] {name} server failed to start on port {port}. Skipping.")
        return stats

    # Warm-up
    print(f"    Warming up ({WARMUP_REQUESTS} requests)...")
    send_requests(url, WARMUP_REQUESTS, CONCURRENCY)

    # Measured runs
    for i in range(MEASURED_RUNS):
        carbon_before = eco.total_carbon
        with eco.track_block(f"{name}_load_test_{i}"):
            t0 = time.perf_counter()
            load_results = send_requests(url, NUM_REQUESTS, CONCURRENCY)
            duration = time.perf_counter() - t0

        carbon_delta = eco.total_carbon - carbon_before
        stats.add_run(
            duration=duration,
            carbon_gco2=carbon_delta,
            rps=load_results["rps"],
            latency_p50_ms=load_results["latency_p50_ms"],
            latency_p99_ms=load_results["latency_p99_ms"],
        )

        print(f"    Run {i+1}/{MEASURED_RUNS}: {duration:.2f}s | "
              f"{carbon_delta:.8f} gCO2 | {load_results['rps']:.0f} req/s | "
              f"p50={load_results['latency_p50_ms']:.1f}ms")

        time.sleep(0.5)

    return stats


def main():
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: Web Framework Carbon Cost Per Request")
    print("=" * 70)

    frameworks = {}
    if _check_available("flask"):
        frameworks["flask"] = run_flask_server
    if _check_available("fastapi") and _check_available("uvicorn"):
        frameworks["fastapi"] = run_fastapi_server

    if not frameworks:
        print("\n[!] No web frameworks installed.")
        print("    Install with: pip install flask  OR  pip install fastapi uvicorn")
        sys.exit(1)

    env = EnvironmentSnapshot(extra_packages=["flask", "fastapi", "uvicorn", "django"])
    eco = EcoTrace(check_updates=False, run_label="WebFramework-Benchmark")
    results = {}

    for name, server_fn in frameworks.items():
        port = FRAMEWORK_PORTS.get(name, 8890)
        print(f"\n{'-' * 70}")
        print(f"  {name.upper()} -- {NUM_REQUESTS} requests x {MEASURED_RUNS} runs (port {port})")
        print(f"{'-' * 70}")
        results[name] = benchmark_framework(name, server_fn, port, eco)

    # --- Summary ---
    print(f"\n{'=' * 70}")
    print(f"  RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n  {'Framework':<15} {'Duration (s)':>14} {'Carbon (gCO2)':>18} "
          f"{'Req/s':>10} {'p50 (ms)':>10}")
    print(f"  {'-' * 70}")

    for name, stats in results.items():
        s = stats.summarize()
        rps = s.get("rps", {}).get("mean", 0)
        p50 = s.get("latency_p50_ms", {}).get("mean", 0)
        print(f"  {name:<15} {s['duration_s']['mean']:>14.4f} "
              f"{s['carbon_gco2']['mean']:>18.10f} {rps:>10.0f} {p50:>10.1f}")

    # Save
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "environment": env.to_dict(),
        "config": {"num_requests": NUM_REQUESTS, "concurrency": CONCURRENCY,
                   "measured_runs": MEASURED_RUNS},
        "statistics": {name: stats.summarize() for name, stats in results.items()},
    }
    labels = list(results.keys())
    if len(labels) >= 2:
        output["comparison"] = results[labels[0]].compare(results[labels[1]])

    output_path = os.path.join(RESULTS_DIR, "04_web_frameworks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
