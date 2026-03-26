import multiprocessing
import time
import math
from ecotrace import EcoTrace

# Initialize EcoTrace with hardware detection
eco = EcoTrace(region_code="TR")

@eco.track
def cpu_stress_benchmark():
    """Stress test that spawns process for every available CPU core.
    
    Purpose: Demonstrate v0.5.0 core normalization engine
    keeping graphs within 0-100% range under extreme multi-core load.
    """
    print(f"[Stress Test] Starting multi-core stress on {multiprocessing.cpu_count()} cores...")
    
    def heavy_computation(duration):
        """CPU-intensive mathematical operation."""
        start = time.time()
        while time.time() - start < duration:
            # Heavy mathematical load that uses CPU heavily
            _ = sum(math.sqrt(i) for i in range(10000))
    
    # Spawn process for every available CPU core
    processes = []
    stress_duration = 5  # 5 seconds of intense load
    
    for core_id in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=heavy_computation, args=(stress_duration,))
        processes.append(p)
        p.start()
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    print(f"[Stress Test] Completed {stress_duration}s stress on all cores")
    return f"Stressed {multiprocessing.cpu_count()} cores for {stress_duration}s"

def main():
    print("=" * 60)
    print("      ECOTRACE v0.5.0 - MULTI-CORE STRESS TEST")
    print("=" * 60)
    print()
    
    # Run the extreme multi-core stress test
    cpu_stress_benchmark()
    
    # Generate comprehensive PDF report
    report_name = "Stress_Test_Report.pdf"
    print(f"\n[Report] Generating {report_name}...")
    
    # Get all CPU samples for chart generation
    all_samples = list(eco._cpu_samples)
    
    eco.generate_pdf_report(
        filename=report_name,
        cpu_samples=all_samples
    )
    
    print()
    print("=" * 60)
    print("STRESS TEST COMPLETED!")
    print(f"Check '{report_name}' for normalized CPU graphs.")
    print("The graph should stay within 0-100% despite extreme load.")
    print("=" * 60)

if __name__ == "__main__":
    # Windows multiprocessing support
    multiprocessing.freeze_support()
    main()
