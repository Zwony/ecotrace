"""
================================================================================
EcoTrace Green Computing Benchmark Series - Case 05: LLM Inference
================================================================================
Quantifies the per-token energy cost and carbon footprint of language model
inference across different model sizes (GPT-2 family).
================================================================================
"""

import os
import sys
import time
import json
import gc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ecotrace import EcoTrace
from benchmarks.framework import EnvironmentSnapshot, BenchmarkStatistics

# --- Configuration -----------------------------------------------------------
# CPU-only: limited to GPT-2 small to keep runtime reasonable.
# For GPT-2 Medium and Large, run on a CUDA GPU. The script gracefully skips
# models that are too slow on the host hardware.
MODELS = [
    {"name": "gpt2",        "label": "GPT-2 Small (124M)",  "params": "124M"},
    # {"name": "gpt2-medium", "label": "GPT-2 Medium (355M)", "params": "355M"},
    # {"name": "gpt2-large",  "label": "GPT-2 Large (774M)",  "params": "774M"},
]

# Test prompts -- identical for all models
PROMPTS = [
    "The impact of renewable energy on global carbon emissions is",
    "Machine learning models consume significant computational resources because",
    "The relationship between software efficiency and environmental sustainability",
    "In the context of green computing, optimizing algorithms can lead to",
    "Data centers around the world are responsible for approximately",
]

NUM_PROMPTS = len(PROMPTS)
MAX_NEW_TOKENS = 30  # Reduced from 50 for CPU feasibility
MEASURED_RUNS = 2     # Reduced from 3 for CPU feasibility
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def _check_transformers():
    try:
        import transformers
        return True
    except ImportError:
        return False


def run_inference(model_name: str, prompts: list, max_new_tokens: int = MAX_NEW_TOKENS):
    """Runs inference on all prompts using the specified model.

    Returns:
        dict: Metrics including total tokens generated, latency, etc.
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    model.eval()

    total_input_tokens = 0
    total_output_tokens = 0
    total_latency = 0.0

    with torch.no_grad():
        for prompt in prompts:
            inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(device)
            input_len = inputs["input_ids"].shape[1]
            total_input_tokens += input_len

            t0 = time.perf_counter()
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=1.0,
            )
            latency = time.perf_counter() - t0

            output_len = outputs.shape[1] - input_len
            total_output_tokens += output_len
            total_latency += latency

    # Cleanup to free VRAM for the next model
    del model
    del tokenizer
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    total_tokens = total_input_tokens + total_output_tokens
    return {
        "total_tokens": total_tokens,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_latency_s": total_latency,
        "tokens_per_second": total_output_tokens / total_latency if total_latency > 0 else 0,
    }


def main():
    print("=" * 70)
    print(" ECOTRACE BENCHMARK: LLM Inference Carbon Footprint (GPT-2 Family)")
    print("=" * 70)

    if not _check_transformers():
        print("\n[!] Hugging Face Transformers is not installed.")
        print("    Install with: pip install transformers torch")
        sys.exit(1)

    env = EnvironmentSnapshot(extra_packages=["transformers", "torch", "accelerate"])
    eco = EcoTrace(check_updates=False, run_label="LLM-Inference-Benchmark")

    all_results = {}

    for model_cfg in MODELS:
        model_name = model_cfg["name"]
        label = model_cfg["label"]

        print(f"\n{'-' * 70}")
        print(f"  {label} -- {NUM_PROMPTS} prompts x {MEASURED_RUNS} runs")
        print(f"{'-' * 70}")

        stats = BenchmarkStatistics(label)

        for i in range(MEASURED_RUNS):
            carbon_before = eco.total_carbon
            with eco.track_block(f"{model_name}_inference_run_{i}"):
                t0 = time.perf_counter()
                metrics = run_inference(model_name, PROMPTS)
                duration = time.perf_counter() - t0

            carbon_delta = eco.total_carbon - carbon_before
            carbon_per_1k_tokens = (
                (carbon_delta / metrics["total_tokens"]) * 1000
                if metrics["total_tokens"] > 0 else 0
            )

            stats.add_run(
                duration=duration,
                carbon_gco2=carbon_delta,
                total_tokens=float(metrics["total_tokens"]),
                tokens_per_second=metrics["tokens_per_second"],
                carbon_per_1k_tokens=carbon_per_1k_tokens,
            )

            print(f"  Run {i+1}/{MEASURED_RUNS}: {duration:.2f}s | "
                  f"{carbon_delta:.8f} gCO2 | "
                  f"{metrics['tokens_per_second']:.1f} tok/s | "
                  f"{carbon_per_1k_tokens:.8f} gCO2/1K tok")

            time.sleep(2.0)  # Cooldown between runs

        all_results[model_name] = {"stats": stats, "config": model_cfg}

    # --- Summary ---
    print(f"\n{'=' * 70}")
    print(f"  RESULTS SUMMARY -- Per-Token Carbon Economics")
    print(f"{'=' * 70}")
    print(f"\n  {'Model':<25} {'Params':>8} {'Duration (s)':>14} {'gCO2/1K tokens':>18} {'Tok/s':>8}")
    print(f"  {'-' * 78}")

    for model_name, data in all_results.items():
        s = data["stats"].summarize()
        params = data["config"]["params"]
        co2_per_1k = s.get("carbon_per_1k_tokens", {}).get("mean", 0)
        tps = s.get("tokens_per_second", {}).get("mean", 0)
        print(f"  {data['config']['label']:<25} {params:>8} "
              f"{s['duration_s']['mean']:>14.2f} {co2_per_1k:>18.8f} {tps:>8.1f}")

    # Scaling analysis
    if len(all_results) >= 2:
        labels = list(all_results.keys())
        small = all_results[labels[0]]["stats"]
        large = all_results[labels[-1]]["stats"]
        comp = small.compare(large)
        print(f"\n  SCALING ANALYSIS (Smallest vs Largest):")
        print(f"    Carbon Increase: {abs(comp['carbon_reduction_pct']):.1f}%")

    # Save
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "environment": env.to_dict(),
        "config": {"models": MODELS, "num_prompts": NUM_PROMPTS,
                   "max_new_tokens": MAX_NEW_TOKENS, "measured_runs": MEASURED_RUNS},
        "statistics": {name: data["stats"].summarize() for name, data in all_results.items()},
    }
    output_path = os.path.join(RESULTS_DIR, "05_llm_inference.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
