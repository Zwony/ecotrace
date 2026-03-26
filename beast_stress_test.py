import multiprocessing
import time
import math
from ecotrace import EcoTrace

# Initialize EcoTrace with hardware detection
eco = EcoTrace(region_code="TR")

def heavy_computation(duration):
    """CPU-intensive mathematical operation for stress testing."""
    start = time.time()
    while time.time() - start < duration:
        # Heavy mathematical load that maximizes CPU usage
        _ = sum(math.sqrt(i) for i in range(15000))

@eco.track
def beast_stress_test():
    """The 'Beast' Stress Test - Maximize all 20 cores of i7-13700H.
    
    Purpose: Demonstrate v0.5.0 core normalization engine
    keeping graphs within 0-100% range under extreme multi-core load.
    """
    print(f"[BEAST TEST] Starting extreme stress on {multiprocessing.cpu_count()} cores...")
    
    # Use multiprocessing.Pool to maximize all cores efficiently
    stress_duration = 5  # 5 seconds of intense load
    
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        # Map heavy computation to all available cores
        results = pool.starmap(heavy_computation, [(stress_duration,)] * multiprocessing.cpu_count())
        pool.close()
        pool.join()
    
    print(f"[BEAST TEST] Completed {stress_duration}s extreme stress on all cores")
    return f"Beast mode: {multiprocessing.cpu_count()} cores @ {stress_duration}s"

def main():
    print("=" * 60)
    print("      ECOTRACE v0.5.0 - THE BEAST STRESS TEST")
    print("=" * 60)
    print()
    
    # Run the extreme multi-core stress test
    beast_stress_test()
    
    # Generate comprehensive PDF report
    report_name = "v5_Stress_Report.pdf"
    print(f"\n[Report] Generating {report_name}...")
    
    # Get all CPU samples for chart generation
    all_samples = list(eco._cpu_samples)
    
    eco.generate_pdf_report(
        filename=report_name,
        cpu_samples=all_samples
    )
    
    print()
    print("=" * 60)
    print("BEAST MODE COMPLETED!")
    print(f"Check '{report_name}' for normalized CPU graphs.")
    print("The graph proves v0.5.0 keeps usage within 0-100% range.")
    print("=" * 60)

if __name__ == "__main__":
    # Windows multiprocessing support
    multiprocessing.freeze_support()
    main()
