import time
import math
from ecotrace import EcoTrace

def main():
    # Initialize EcoTrace
    eco = EcoTrace(region_code="TR")
    
    @eco.track
    def light_task():
        """A simple, single-threaded task to show Single-Thread Intensive insights."""
        print("\n[LIGHT TEST] running 2-second single-threaded mathematical task...")
        start = time.time()
        while time.time() - start < 2:
            [math.sqrt(i) for i in range(1000)]
        
    light_task()
    
    # Generate report (v0.5.1 automatically includes charts)
    eco.generate_pdf_report("v5_LIGHT_report.pdf")
    print("\n[LIGHT TEST DONE] Check 'v5_LIGHT_report.pdf' for Single-Thread Intensive metrics.")

if __name__ == "__main__":
    main()
