import time
from ecotrace import EcoTrace

# Setting a very low limit to trigger the budget warning
eco = EcoTrace(region_code="US", carbon_limit=0.000000001)

@eco.track
def heavy_task():
    for _ in range(5):
        time.sleep(0.1)

if __name__ == "__main__":
    heavy_task()
