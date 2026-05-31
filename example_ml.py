import time
from ecotrace.ml import ecotrace_ml 

@ecotrace_ml(model_name="ai_model", gpu_index=0, sample_interval=1.0)
def model_training_simulation():
    print("\n[SIMULATION] Training AI model...")
    for i in range(1, 5):
        print(f"Epoch {i}/4 running... Monitoring hardware footprint in the background.")
        time.sleep(1)

if __name__ == "__main__":
    model_training_simulation()
