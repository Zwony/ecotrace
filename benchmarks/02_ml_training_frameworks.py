"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 02: ML Training Frameworks
================================================================================
Compares energy consumption and carbon emissions of PyTorch vs TensorFlow
for training an identical CNN architecture on CIFAR-10.
================================================================================
"""

import os
import sys
import time
import json

# Ensure local ecotrace package is resolvable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ecotrace import EcoTrace
from benchmarks.framework import EnvironmentSnapshot, BenchmarkStatistics

# --- Configuration -----------------------------------------------------------
NUM_EPOCHS = 5
BATCH_SIZE = 64
LEARNING_RATE = 0.001
MEASURED_RUNS = 3  # Full training runs (expensive, so fewer repetitions)
WARMUP_RUNS = 0    # No warm-up for full training benchmarks
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def _check_torch_available():
    try:
        import torch
        return True
    except ImportError:
        return False


def _check_tf_available():
    try:
        import tensorflow
        return True
    except ImportError:
        return False


def train_pytorch_cnn(num_epochs=NUM_EPOCHS, batch_size=BATCH_SIZE):
    """Trains a simple CNN on CIFAR-10 using PyTorch.

    Returns:
        dict: Metrics including final accuracy and loss.
    """
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    import torchvision
    import torchvision.transforms as transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])

    trainset = torchvision.datasets.CIFAR10(
        root="./data", train=True, download=True, transform=transform
    )
    trainloader = DataLoader(trainset, batch_size=batch_size, shuffle=True, num_workers=0)

    testset = torchvision.datasets.CIFAR10(
        root="./data", train=False, download=True, transform=transform
    )
    testloader = DataLoader(testset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Simple CNN (LeNet-5 inspired)
    class SimpleCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            )
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(64 * 8 * 8, 256), nn.ReLU(), nn.Dropout(0.5),
                nn.Linear(256, 10),
            )

        def forward(self, x):
            return self.classifier(self.features(x))

    model = SimpleCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Training loop
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for inputs, labels in trainloader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

    # Evaluation
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for inputs, labels in testloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = correct / total * 100
    return {"accuracy": accuracy, "final_loss": running_loss / len(trainloader)}


def train_tensorflow_cnn(num_epochs=NUM_EPOCHS, batch_size=BATCH_SIZE):
    """Trains an identical CNN on CIFAR-10 using TensorFlow/Keras.

    Returns:
        dict: Metrics including final accuracy and loss.
    """
    import tensorflow as tf

    # Suppress TF info logs
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()
    x_train = x_train.astype("float32") / 255.0
    x_test = x_test.astype("float32") / 255.0

    # Normalize with same stats as PyTorch
    mean_vals = [0.4914, 0.4822, 0.4465]
    std_vals = [0.2470, 0.2435, 0.2616]
    for i in range(3):
        x_train[..., i] = (x_train[..., i] - mean_vals[i]) / std_vals[i]
        x_test[..., i] = (x_test[..., i] - mean_vals[i]) / std_vals[i]

    # Same architecture as PyTorch model
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, 3, padding="same", activation="relu", input_shape=(32, 32, 3)),
        tf.keras.layers.MaxPooling2D(2),
        tf.keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
        tf.keras.layers.MaxPooling2D(2),
        tf.keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(10),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"],
    )

    history = model.fit(
        x_train, y_train,
        epochs=num_epochs,
        batch_size=batch_size,
        validation_data=(x_test, y_test),
        verbose=0,
    )

    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
    return {"accuracy": test_acc * 100, "final_loss": test_loss}


def main():
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: PyTorch vs TensorFlow (Energy & Carbon Efficiency)")
    print("=" * 70)

    has_torch = _check_torch_available()
    has_tf = _check_tf_available()

    if not has_torch and not has_tf:
        print("\n[!] Neither PyTorch nor TensorFlow is installed.")
        print("    Install with: pip install torch  OR  pip install tensorflow")
        sys.exit(1)

    env = EnvironmentSnapshot(extra_packages=["torch", "tensorflow", "torchvision"])
    eco = EcoTrace(check_updates=False, run_label="ML-Framework-Benchmark")

    results = {}

    if has_torch:
        print(f"\n{'-' * 70}")
        print(f" PYTORCH TRAINING ({NUM_EPOCHS} epochs x {MEASURED_RUNS} runs)")
        print(f"{'-' * 70}")
        stats_pt = BenchmarkStatistics("pytorch")

        for i in range(MEASURED_RUNS):
            carbon_before = eco.total_carbon
            with eco.track_block(f"pytorch_training_run_{i}"):
                t0 = time.perf_counter()
                metrics = train_pytorch_cnn()
                duration = time.perf_counter() - t0

            carbon_delta = eco.total_carbon - carbon_before
            stats_pt.add_run(duration=duration, carbon_gco2=carbon_delta,
                             accuracy=metrics["accuracy"], final_loss=metrics["final_loss"])
            print(f"  Run {i+1}/{MEASURED_RUNS}: {duration:.2f}s | "
                  f"{carbon_delta:.8f} gCO2 | Acc: {metrics['accuracy']:.2f}%")
            time.sleep(1.0)

        results["pytorch"] = stats_pt

    if has_tf:
        print(f"\n{'-' * 70}")
        print(f" TENSORFLOW TRAINING ({NUM_EPOCHS} epochs x {MEASURED_RUNS} runs)")
        print(f"{'-' * 70}")
        stats_tf = BenchmarkStatistics("tensorflow")

        for i in range(MEASURED_RUNS):
            carbon_before = eco.total_carbon
            with eco.track_block(f"tensorflow_training_run_{i}"):
                t0 = time.perf_counter()
                metrics = train_tensorflow_cnn()
                duration = time.perf_counter() - t0

            carbon_delta = eco.total_carbon - carbon_before
            stats_tf.add_run(duration=duration, carbon_gco2=carbon_delta,
                             accuracy=metrics["accuracy"], final_loss=metrics["final_loss"])
            print(f"  Run {i+1}/{MEASURED_RUNS}: {duration:.2f}s | "
                  f"{carbon_delta:.8f} gCO2 | Acc: {metrics['accuracy']:.2f}%")
            time.sleep(1.0)

        results["tensorflow"] = stats_tf

    # --- Summary ---
    print(f"\n{'=' * 70}")
    print(f" RESULTS SUMMARY")
    print(f"{'=' * 70}")

    for label, stats in results.items():
        s = stats.summarize()
        print(f"\n  {label.upper()}:")
        print(f"    Duration : {s['duration_s']['mean']:.2f}s +/- {s['duration_s']['std_dev']:.2f}s")
        print(f"    Carbon   : {s['carbon_gco2']['mean']:.8f} gCO2 +/- {s['carbon_gco2']['std_dev']:.8f}")
        if "accuracy" in s:
            print(f"    Accuracy : {s['accuracy']['mean']:.2f}%")

    if has_torch and has_tf and "pytorch" in results and "tensorflow" in results:
        comp = results["pytorch"].compare(results["tensorflow"])
        print(f"\n  COMPARISON (PyTorch as baseline):")
        print(f"    Speedup: {comp['speedup_ratio']:.2f}x")
        print(f"    Carbon Reduction: {comp['carbon_reduction_pct']:.1f}%")
        sig = "[OK] Significant" if comp['duration_test']['significant_at_05'] else "[X] Not significant"
        print(f"    Statistical Significance: {sig}")

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "environment": env.to_dict(),
        "config": {"epochs": NUM_EPOCHS, "batch_size": BATCH_SIZE, "lr": LEARNING_RATE,
                   "measured_runs": MEASURED_RUNS},
        "statistics": {label: stats.summarize() for label, stats in results.items()},
    }
    if has_torch and has_tf and "pytorch" in results and "tensorflow" in results:
        output["comparison"] = results["pytorch"].compare(results["tensorflow"])

    output_path = os.path.join(RESULTS_DIR, "02_ml_training_frameworks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
