import multiprocessing
import time
import math
from ecotrace import EcoTrace

def heavy_computation(duration):
    """CPU-intensive task for multi-core stress testing."""
    start = time.time()
    while time.time() - start < duration:
        [math.sqrt(i) for i in range(50000)]

def main():
    # Initialize EcoTrace
    eco = EcoTrace(region_code="TR")
    
    @eco.track
    def beast_mode_test():
        """Saturate all cores to show v0.5.1 core normalization."""
        print(f"\n[BEAST MODE] saturating {multiprocessing.cpu_count()} cores for 10 seconds...")
        
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            # Distribute load to ALL logical cores
            pool.map(heavy_computation, [10] * multiprocessing.cpu_count())
            pool.close()
            pool.join()
        
    beast_mode_test()
    
    # Generate report (v0.5.1 automatically includes charts)
    eco.generate_pdf_report("v5_STRESS_report.pdf")
    print("\n[STRESS TEST DONE] Check 'v5_STRESS_report.pdf' for normalized graphs.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
